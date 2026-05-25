from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


def confirm(parent: QWidget, title: str, message: str) -> bool:
    """Show a confirmation dialog."""
    result = QMessageBox.question(parent, title, message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    return result == QMessageBox.Yes

