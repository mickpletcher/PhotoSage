from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem


class PreviewTable(QTableWidget):
    """Main preview table for proposed rename operations."""

    row_selected = Signal(dict)
    row_data_role = Qt.UserRole + 1

    columns = [
        "Thumbnail",
        "Original Filename",
        "Proposed Filename",
        "Metadata Score",
        "AI Used",
        "Provider",
        "Status",
        "Approval",
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
        self.verticalHeader().setDefaultSectionSize(24)
        self.horizontalHeader().setStretchLastSection(True)
        self.itemSelectionChanged.connect(self._emit_selection)

    def load_rows(self, rows: list[dict[str, Any]]) -> None:
        self.setUpdatesEnabled(False)
        self.setSortingEnabled(False)
        self.rows = rows
        self.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            ai_response = row.get("ai_response") or {}
            metadata = row.get("metadata") or {}
            values = [
                row.get("thumbnail_path", ""),
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
            values.insert(7, row.get("approval_status", "not-required"))
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(self.row_data_role, row)
                if column != 2:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(self._status_color(row))
                self.setItem(row_index, column, item)
        self.setSortingEnabled(True)
        self.setUpdatesEnabled(True)

    def filter_text(self, text: str) -> None:
        query = text.lower().strip()
        for row_index in range(self.rowCount()):
            haystack = " ".join(self.item(row_index, column).text() for column in range(self.columnCount())).lower()
            self.setRowHidden(row_index, query not in haystack)

    def set_selected_approval(self, approval: str) -> None:
        for model_index in self.selectionModel().selectedRows():
            row_index = model_index.row()
            row = self.item(row_index, 0).data(self.row_data_role)
            row["approval_status"] = approval
            self.item(row_index, 7).setText(approval)

    def review_decisions(self) -> list[dict[str, str]]:
        decisions: list[dict[str, str]] = []
        for row_index in range(self.rowCount()):
            row = self.item(row_index, 0).data(self.row_data_role)
            selector = str(row["original_path"])
            proposed = self.item(row_index, 2).text().strip()
            if row.get("approval_status") == "rejected" and row.get("status") != "rejected":
                decisions.append({"selector": selector, "action": "reject"})
            elif proposed != row.get("new_filename"):
                decisions.append({"selector": selector, "action": "edit", "new_filename": proposed})
            elif row.get("approval_status") == "approved" and row.get("status") == "needs-review":
                decisions.append({"selector": selector, "action": "approve"})
        return decisions

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
        row = selected[0].data(self.row_data_role)
        if row:
            self.row_selected.emit(row)
