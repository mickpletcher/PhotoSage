from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLineEdit, QPushButton, QWidget


class FolderPicker(QWidget):
    """Folder picker with drag and drop support."""

    folder_changed = Signal(Path)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select or drop a photo folder")
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.path_edit, 1)
        layout.addWidget(self.browse_button)

    def folder(self) -> Path | None:
        text = self.path_edit.text().strip()
        return Path(text) if text else None

    def set_folder(self, path: Path) -> None:
        self.path_edit.setText(str(path))
        self.folder_changed.emit(path)

    def browse(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Select Photo Folder")
        if selected:
            self.set_folder(Path(selected))

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_dir():
                self.set_folder(path)
                break

