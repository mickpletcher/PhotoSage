from pathlib import Path

from PIL import Image

from photosage.config import AppConfig
from photosage.watch.folder_watcher import build_approval_queue, process_watch_once


def _image(path: Path) -> None:
    Image.new("RGB", (16, 16), (30, 60, 90)).save(path)


def test_watch_builds_approval_queue_for_stable_files(tmp_path):
    image = tmp_path / "IMG_001.jpg"
    _image(image)
    config = AppConfig(manifest_directory=tmp_path / "manifests", watch_stable_seconds=0, metadata_threshold=0)

    manifest = build_approval_queue(tmp_path, config)

    assert manifest["watch_mode"] is True
    assert manifest["approval_required"] is True
    assert manifest["files"][0]["approval_status"] == "queued"


def test_watch_apply_requires_explicit_apply(tmp_path):
    image = tmp_path / "IMG_001.jpg"
    _image(image)
    config = AppConfig(manifest_directory=tmp_path / "manifests", watch_stable_seconds=0, metadata_threshold=0)

    manifest = process_watch_once(tmp_path, config, apply=False)

    assert image.exists()
    assert manifest["approval_required"] is True
