from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QDir, QThread, Qt
from PySide6.QtWidgets import (
    QFileSystemModel,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from photosage.config import AppConfig, save_config
from photosage.gui.dialogs.confirm_dialog import confirm
from photosage.gui.dialogs.settings_dialog import SettingsDialog
from photosage.gui.dialogs.undo_dialog import UndoDialog
from photosage.gui.widgets.ai_panel import AiPanel
from photosage.gui.widgets.folder_picker import FolderPicker
from photosage.gui.widgets.image_preview import ImagePreview
from photosage.gui.widgets.log_console import LogConsole
from photosage.gui.widgets.metadata_panel import MetadataPanel
from photosage.gui.widgets.preview_table import PreviewTable
from photosage.gui.widgets.progress_panel import ProgressPanel
from photosage.gui.widgets.provider_selector import ProviderSelector
from photosage.gui.workers.preview_worker import PreviewWorker
from photosage.gui.workers.rename_worker import RenameWorker
from photosage.gui.workers.scan_worker import ScanWorker
from photosage.gui.workers.undo_worker import UndoWorker


class MainWindow(QMainWindow):
    """Main PhotoSage desktop window."""

    def __init__(self, config: AppConfig, config_path: Path) -> None:
        super().__init__()
        self.config = config
        self.config_path = config_path
        self.current_thread: QThread | None = None
        self.current_worker = None
        self.preview_ready = False
        self.pending_undo_manifest: Path | None = None
        self.setWindowTitle("PhotoSage")
        self.resize(1440, 900)
        self._build_ui()

    def _build_ui(self) -> None:
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)
        self.folder_picker = FolderPicker()
        toolbar.addWidget(self.folder_picker)
        self.provider_selector = ProviderSelector()
        self.provider_selector.load_from_config(self.config)
        toolbar.addWidget(self.provider_selector)

        self.scan_button = QPushButton("Scan")
        self.preview_button = QPushButton("Preview")
        self.rename_button = QPushButton("Apply Rename")
        self.undo_button = QPushButton("Undo Last Rename")
        self.settings_button = QPushButton("Settings")
        for button in [self.scan_button, self.preview_button, self.rename_button, self.undo_button, self.settings_button]:
            toolbar.addWidget(button)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search preview rows")
        toolbar.addWidget(self.search)

        self.folder_model = QFileSystemModel()
        self.folder_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.folder_model.setRootPath("")
        self.folder_tree = QTreeView()
        self.folder_tree.setModel(self.folder_model)
        self.folder_tree.setHeaderHidden(True)
        self.folder_tree.setMinimumWidth(220)
        self.folder_tree.clicked.connect(self._folder_tree_selected)

        self.preview_table = PreviewTable()
        self.image_preview = ImagePreview()
        self.metadata_panel = MetadataPanel()
        self.ai_panel = AiPanel()
        self.reasoning_panel = QLabel("Select a file to inspect filename reasoning.")
        self.reasoning_panel.setWordWrap(True)

        detail_tabs = QTabWidget()
        detail_tabs.addTab(self.image_preview, "Image")
        detail_tabs.addTab(self.metadata_panel, "Metadata")
        detail_tabs.addTab(self.ai_panel, "AI Analysis")
        detail_tabs.addTab(self.reasoning_panel, "Reasoning")
        detail_tabs.setMinimumWidth(320)

        center_splitter = QSplitter(Qt.Horizontal)
        center_splitter.addWidget(self.folder_tree)
        center_splitter.addWidget(self.preview_table)
        center_splitter.addWidget(detail_tabs)
        center_splitter.setStretchFactor(1, 1)

        self.log_console = LogConsole()
        self.progress_panel = ProgressPanel()

        main_layout = QVBoxLayout()
        main_layout.addWidget(center_splitter, 1)
        main_layout.addWidget(self.log_console, 0)
        main_layout.addWidget(self.progress_panel)

        central = QWidget()
        central.setLayout(main_layout)
        self.setCentralWidget(central)

        self.scan_button.clicked.connect(self.scan)
        self.preview_button.clicked.connect(self.preview)
        self.rename_button.clicked.connect(self.apply_rename)
        self.undo_button.clicked.connect(self.open_undo_dialog)
        self.settings_button.clicked.connect(self.open_settings)
        self.search.textChanged.connect(self.preview_table.filter_text)
        self.preview_table.row_selected.connect(self.show_row_details)
        self.progress_panel.cancel_button.clicked.connect(self.cancel_current_worker)

    def selected_folder(self) -> Path | None:
        folder = self.folder_picker.folder()
        if folder and folder.exists():
            return folder
        QMessageBox.warning(self, "Folder Required", "Select a valid photo folder first.")
        return None

    def apply_controls_to_config(self) -> None:
        self.provider_selector.apply_to_config(self.config)
        save_config(self.config, self.config_path)

    def scan(self) -> None:
        folder = self.selected_folder()
        if not folder:
            return
        self.apply_controls_to_config()
        worker = ScanWorker(folder, self.config, self.config.recursive_scanning, self.provider_selector.force_ai.isChecked())
        self._start_worker(worker, worker.finished, self.scan_finished)

    def preview(self) -> None:
        folder = self.selected_folder()
        if not folder:
            return
        self.apply_controls_to_config()
        worker = PreviewWorker(folder, self.config, self.config.recursive_scanning, self.provider_selector.force_ai.isChecked())
        self._start_worker(worker, worker.finished, self.preview_finished)

    def apply_rename(self) -> None:
        folder = self.selected_folder()
        if not folder:
            return
        if not self.preview_ready:
            QMessageBox.warning(self, "Preview Required", "Run Preview before applying renames.")
            return
        if not confirm(self, "Apply Rename", "Rename files now? A manifest will be written before changes are applied."):
            return
        self.apply_controls_to_config()
        worker = RenameWorker(folder, self.config, self.config.recursive_scanning)
        self._start_worker(worker, worker.finished, self.rename_finished)

    def open_undo_dialog(self) -> None:
        dialog = UndoDialog(self.config.manifest_directory, self)
        dialog.manifest_selected.connect(self.preview_undo)
        dialog.exec()

    def preview_undo(self, manifest_path: Path) -> None:
        self.pending_undo_manifest = manifest_path
        worker = UndoWorker(manifest_path, dry_run=True)
        self._start_worker(worker, worker.finished, self.undo_preview_finished)

    def run_undo(self, manifest_path: Path) -> None:
        worker = UndoWorker(manifest_path, dry_run=False)
        self._start_worker(worker, worker.finished, self.undo_finished)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.config, self.config_path, self)
        if dialog.exec():
            self.provider_selector.load_from_config(self.config)
            self.log_console.append_line("Settings saved.")

    def scan_finished(self, result: dict[str, Any]) -> None:
        self.preview_ready = False
        self.preview_table.load_rows(result["files"])
        self.log_console.append_line(f"Scan complete: {result['summary']}")

    def preview_finished(self, manifest: dict[str, Any]) -> None:
        self.preview_ready = True
        self.preview_table.load_rows(manifest["files"])
        self.log_console.append_line(f"Preview complete. Manifest: {manifest.get('manifest_path')}")

    def rename_finished(self, manifest: dict[str, Any]) -> None:
        self.preview_ready = False
        self.preview_table.load_rows(manifest["files"])
        self.log_console.append_line(f"Rename complete. Manifest: {manifest.get('manifest_path')}")

    def undo_preview_finished(self, report: dict[str, Any]) -> None:
        self.log_console.append_line(f"Undo preview: {report['summary']}")
        if self.pending_undo_manifest and confirm(self, "Confirm Undo", f"Rollback preview complete:\n{report['summary']}\n\nRestore files now?"):
            self.run_undo(self.pending_undo_manifest)

    def undo_finished(self, report: dict[str, Any]) -> None:
        self.log_console.append_line(f"Undo complete. Report: {report.get('report_path')}")

    def show_row_details(self, row: dict[str, Any]) -> None:
        metadata = row.get("metadata") or {}
        ai_response = row.get("ai_response") or {}
        self.metadata_panel.set_metadata(metadata)
        self.ai_panel.set_ai_response(ai_response)
        path = row.get("original_path") or row.get("path")
        if path:
            self.image_preview.load_image(Path(path))
        self.reasoning_panel.setText(
            f"Score: {row.get('metadata_score')}\n"
            f"AI required: {row.get('ai_required')}\n"
            f"AI used: {row.get('ai_used')}\n"
            f"Proposed filename: {row.get('new_filename', '')}"
        )

    def _start_worker(self, worker, finished_signal, finished_slot) -> None:
        self.cancel_current_worker()
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self.progress_panel.set_status)
        worker.failed.connect(self.worker_failed)
        finished_signal.connect(finished_slot)
        finished_signal.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self.current_thread = thread
        self.current_worker = worker
        thread.start()

    def cancel_current_worker(self) -> None:
        if self.current_worker and hasattr(self.current_worker, "cancel"):
            self.current_worker.cancel()

    def worker_failed(self, message: str) -> None:
        self.log_console.append_line(f"ERROR: {message}")
        QMessageBox.critical(self, "Operation Failed", message)

    def _folder_tree_selected(self, index) -> None:
        path = Path(self.folder_model.filePath(index))
        if path.is_dir():
            self.folder_picker.set_folder(path)

