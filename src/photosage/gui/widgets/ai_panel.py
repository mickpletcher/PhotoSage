from __future__ import annotations

import json

from PySide6.QtWidgets import QTextEdit


class AiPanel(QTextEdit):
    """Read-only AI classification detail panel."""

    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)

    def set_ai_response(self, response: dict) -> None:
        self.setPlainText(json.dumps(response or {}, indent=2, default=str))

