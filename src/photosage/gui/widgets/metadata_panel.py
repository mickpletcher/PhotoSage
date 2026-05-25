from __future__ import annotations

import json

from PySide6.QtWidgets import QTextEdit


class MetadataPanel(QTextEdit):
    """Read-only metadata detail panel."""

    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)

    def set_metadata(self, metadata: dict) -> None:
        self.setPlainText(json.dumps(metadata or {}, indent=2, default=str))

