from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel


class ImagePreview(QLabel):
    """Image preview widget that loads scaled pixmaps on selection."""

    def __init__(self) -> None:
        super().__init__("No image selected")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(220)
        self.setStyleSheet("border: 1px solid #3a3f4b;")

    def load_image(self, path: Path) -> None:
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self.setText("Preview unavailable")
            return
        self.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

