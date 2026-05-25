from __future__ import annotations

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QPushButton, QTextEdit, QVBoxLayout, QWidget


class LogConsole(QWidget):
    """Simple live log console."""

    def __init__(self) -> None:
        super().__init__()
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.auto_scroll = QCheckBox("Auto-scroll")
        self.auto_scroll.setChecked(True)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.text.clear)

        controls = QHBoxLayout()
        controls.addWidget(self.auto_scroll)
        controls.addStretch(1)
        controls.addWidget(clear_button)

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.text)

    def append_line(self, line: str) -> None:
        self.text.append(line)
        if self.auto_scroll.isChecked():
            self.text.moveCursor(QTextCursor.End)
