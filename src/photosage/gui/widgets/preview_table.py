from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem


class PreviewTable(QTableWidget):
    """Main preview table for proposed rename operations."""

    row_selected = Signal(dict)

    columns = [
        "Thumbnail",
        "Original Filename",
        "Proposed Filename",
        "Metadata Score",
        "AI Used",
        "Provider",
        "Status",
        "Confidence",
        "File Type",
        "Date Taken",
        "Location",
    ]

    def __init__(self) -> None:
        super().__init__(0, len(self.columns))
        self.rows: list[dict[str, Any]] = []
        self.setHorizontalHeaderLabels(self.columns)
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.itemSelectionChanged.connect(self._emit_selection)

    def load_rows(self, rows: list[dict[str, Any]]) -> None:
        self.setSortingEnabled(False)
        self.rows = rows
        self.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            ai_response = row.get("ai_response") or {}
            metadata = row.get("metadata") or {}
            values = [
                "",
                row.get("original_filename", ""),
                row.get("new_filename") or row.get("proposed_filename") or "",
                row.get("metadata_score", ""),
                "yes" if row.get("ai_used") or row.get("ai_required") else "no",
                ai_response.get("provider") or row.get("provider", ""),
                row.get("status", ""),
                ai_response.get("confidence") or row.get("confidence", ""),
                row.get("file_type") or Path(str(row.get("original_filename", ""))).suffix.lower().lstrip("."),
                metadata.get("date_taken") or row.get("date_taken", ""),
                row.get("location", ""),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(self._status_color(row))
                self.setItem(row_index, column, item)
        self.setSortingEnabled(True)

    def filter_text(self, text: str) -> None:
        query = text.lower().strip()
        for row_index, row in enumerate(self.rows):
            haystack = " ".join(str(value) for value in row.values()).lower()
            self.setRowHidden(row_index, query not in haystack)

    def _status_color(self, row: dict[str, Any]) -> QColor:
        status = str(row.get("status", ""))
        if status in {"error", "missing", "overwrite-prevented", "failed"}:
            return QColor("#3d1717")
        if row.get("ai_used") or row.get("ai_required"):
            return QColor("#3a3214")
        return QColor("#17351f")

    def _emit_selection(self) -> None:
        selected = self.selectedItems()
        if not selected:
            return
        row_index = selected[0].row()
        if 0 <= row_index < len(self.rows):
            self.row_selected.emit(self.rows[row_index])
