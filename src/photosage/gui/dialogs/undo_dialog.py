from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QFileDialog, QHBoxLayout, QListWidget, QPushButton, QVBoxLayout


class UndoDialog(QDialog):
    """Dialog for choosing a manifest to roll back."""

    manifest_selected = Signal(Path)

    def __init__(self, manifest_directory: Path, parent=None) -> None:
        super().__init__(parent)
        self.manifest_directory = manifest_directory
        self.setWindowTitle("Undo Rename")
        self.setMinimumSize(520, 360)
        self.list_widget = QListWidget()
        self.refresh()

        browse = QPushButton("Browse Manifest")
        browse.clicked.connect(self.browse)
        undo = QPushButton("Undo Selected")
        undo.clicked.connect(self.emit_selected)

        buttons = QHBoxLayout()
        buttons.addWidget(browse)
        buttons.addStretch(1)
        buttons.addWidget(undo)

        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        layout.addLayout(buttons)

    def refresh(self) -> None:
        self.list_widget.clear()
        if not self.manifest_directory.exists():
            return
        for path in sorted(self.manifest_directory.glob("rename_manifest_*.json"), reverse=True):
            self.list_widget.addItem(str(path))

    def browse(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(self, "Select Manifest", str(self.manifest_directory), "JSON (*.json)")
        if selected:
            self.manifest_selected.emit(Path(selected))
            self.accept()

    def emit_selected(self) -> None:
        item = self.list_widget.currentItem()
        if not item:
            return
        self.manifest_selected.emit(Path(item.text()))
        self.accept()

