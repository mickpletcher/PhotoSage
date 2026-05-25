import json

import pytest

from photosage.manifest.manifest_reader import ManifestValidationError, load_manifest, resolved_input_directory, safe_restore_path, validate_manifest
from photosage.manifest.manifest_writer import create_manifest, write_manifest


def test_load_manifest_validates_required_shape(tmp_path):
    manifest = create_manifest(
        input_directory=tmp_path,
        dry_run=False,
        provider_used=None,
        metadata_threshold=70,
        files=[{"original_path": str(tmp_path / "a.jpg"), "new_path": str(tmp_path / "b.jpg"), "status": "renamed"}],
    )
    manifest_path = write_manifest(manifest, tmp_path)

    loaded = load_manifest(manifest_path)

    assert loaded["run_id"] == manifest["run_id"]


def test_load_manifest_rejects_malformed_json(tmp_path):
    manifest_path = tmp_path / "bad.json"
    manifest_path.write_text("{bad json", encoding="utf-8")

    with pytest.raises(ManifestValidationError):
        load_manifest(manifest_path)


def test_validate_manifest_rejects_missing_keys(tmp_path):
    with pytest.raises(ManifestValidationError):
        validate_manifest({"run_id": "x", "files": []}, tmp_path / "manifest.json")


def test_safe_restore_path_rejects_traversal(tmp_path):
    with pytest.raises(ManifestValidationError):
        safe_restore_path(tmp_path / ".." / "escape.jpg", tmp_path)


def test_load_manifest_rejects_path_outside_input_directory(tmp_path):
    outside = tmp_path.parent / "outside.jpg"
    manifest = create_manifest(
        input_directory=tmp_path,
        dry_run=False,
        provider_used=None,
        metadata_threshold=70,
        files=[{"original_path": str(outside), "new_path": str(tmp_path / "b.jpg"), "status": "renamed"}],
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ManifestValidationError):
        load_manifest(manifest_path)


def test_resolved_input_directory_uses_manifest_parent_for_relative_paths(tmp_path):
    manifest_path = tmp_path / "manifests" / "manifest.json"
    manifest_path.parent.mkdir()
    manifest = {"input_directory": "../photos"}

    assert resolved_input_directory(manifest, manifest_path) == (tmp_path / "photos").resolve(strict=False)
