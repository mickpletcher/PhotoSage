import pytest

pytest.importorskip("PySide6.QtWidgets")

from photosage.gui.widgets.preview_table import PreviewTable
from photosage.gui.widgets.provider_selector import ProviderSelector


def test_gui_preview_table_edits_and_approves(qtbot):
    table = PreviewTable()
    qtbot.addWidget(table)
    table.load_rows(
        [
            {
                "original_path": "C:/photos/IMG_001.jpg",
                "original_filename": "IMG_001.jpg",
                "new_filename": "old.jpg",
                "metadata_score": 10,
                "status": "needs-review",
                "approval_status": "required",
            }
        ]
    )
    table.selectRow(0)
    table.set_selected_approval("approved")
    table.item(0, 2).setText("new.jpg")

    decisions = table.review_decisions()

    assert decisions == [{"selector": "C:/photos/IMG_001.jpg", "action": "edit", "new_filename": "new.jpg"}]


def test_gui_provider_selector_includes_kimi(qtbot):
    selector = ProviderSelector()
    qtbot.addWidget(selector)
    assert selector.provider_combo.findText("kimi") >= 0
