from pathlib import Path

from PIL import Image

from photosage.config import AppConfig
from photosage.manifest.manifest_reader import load_manifest
from photosage.rename.renamer import apply_reviewed_manifest, preview_renames


def test_large_batch_plans_unique_destinations(tmp_path):
    for index in range(150):
        Image.new("RGB", (2, 2), (index % 255, 0, 0)).save(tmp_path / f"IMG_{index:04d}.jpg")
    result = preview_renames(tmp_path, AppConfig(manifest_directory=tmp_path / "manifests", metadata_threshold=0))
    names = [item["new_filename"].casefold() for item in result.manifest["files"]]
    assert len(names) == len(set(names)) == 150


def test_post_rename_integrity_failure_restores_source(monkeypatch, tmp_path):
    source = tmp_path / "IMG_001.jpg"
    Image.new("RGB", (8, 8)).save(source)
    result = preview_renames(tmp_path, AppConfig(manifest_directory=tmp_path / "manifests", metadata_threshold=0))
    original_match = __import__("photosage.rename.renamer", fromlist=["_source_matches"])._source_matches
    calls = {"count": 0}

    def mismatch_after_move(item, path: Path):
        calls["count"] += 1
        return original_match(item, path) if calls["count"] == 1 else False

    monkeypatch.setattr("photosage.rename.renamer._source_matches", mismatch_after_move)
    applied = apply_reviewed_manifest(result.manifest_path)

    assert source.exists()
    assert applied.manifest["files"][0]["status"] == "integrity-rollback"
    assert load_manifest(result.manifest_path)["files"][0]["status"] == "integrity-rollback"


def test_locked_source_is_journaled_without_data_loss(monkeypatch, tmp_path):
    source = tmp_path / "IMG_001.jpg"
    Image.new("RGB", (8, 8)).save(source)
    result = preview_renames(tmp_path, AppConfig(manifest_directory=tmp_path / "manifests", metadata_threshold=0))
    original_rename = Path.rename

    def locked(path, target):
        if path == source:
            raise PermissionError("locked")
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rename", locked)
    applied = apply_reviewed_manifest(result.manifest_path)

    assert source.exists()
    assert applied.manifest["files"][0]["status"] == "error"
    assert "locked" in applied.manifest["files"][0]["error"]
