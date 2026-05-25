from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton, QWidget


class ProgressPanel(QWidget):
    """Progress bar with cancel action."""

    def __init__(self) -> None:
        super().__init__()
        self.label = QLabel("Ready")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.cancel_button = QPushButton("Cancel")

        layout = QHBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.progress, 1)
        layout.addWidget(self.cancel_button)

    def set_status(self, percent: int, message: str) -> None:
        self.progress.setValue(percent)
        self.label.setText(message)

