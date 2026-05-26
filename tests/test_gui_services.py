from pathlib import Path
import os
import sys

import pytest
from PIL import Image

from photosage.config import AppConfig
from photosage.gui.services import apply_folder, preview_folder, scan_folder, undo_manifest


def _write_image(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), color="red").save(path)


def test_gui_scan_service_uses_backend_metadata(tmp_path):
    photo = tmp_path / "photos" / "IMG_0001.jpg"
    _write_image(photo)
    (photo.parent / "notes.txt").write_text("skip", encoding="utf-8")
    config = AppConfig(manifest_directory=tmp_path / "manifests")

    result = scan_folder(photo.parent, config)

    assert result["summary"]["supported_files"] == 1
    assert result["summary"]["unsupported_files"] == 1
    assert result["files"][0]["original_filename"] == "IMG_0001.jpg"


def test_gui_preview_apply_and_undo_services_use_backend(tmp_path):
    photo = tmp_path / "photos" / "IMG_0001.jpg"
    _write_image(photo)
    config = AppConfig(manifest_directory=tmp_path / "manifests")

    preview = preview_folder(photo.parent, config)
    applied = apply_folder(photo.parent, config)
    restored = undo_manifest(Path(applied["manifest_path"]))

    assert preview["dry_run"] is True
    assert applied["files"][0]["status"] == "renamed"
    assert restored["summary"]["restored"] == 1
    assert photo.exists()


def test_gui_qt_modules_import_when_pyside_available():
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        pytest.skip("Qt GUI imports are skipped on headless Linux CI.")
    pytest.importorskip("PySide6.QtWidgets")
    import photosage.gui.app  # noqa: F401
    import photosage.gui.main_window  # noqa: F401
