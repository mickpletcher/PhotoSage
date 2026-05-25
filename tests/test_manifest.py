from photosage.manifest.manifest_writer import create_manifest, write_manifest
from photosage.manifest.undo import undo_from_manifest


def test_manifest_creation_and_write(tmp_path):
    manifest = create_manifest(
        input_directory=tmp_path,
        dry_run=True,
        provider_used="anthropic",
        metadata_threshold=70,
        files=[{"original_path": "a.jpg", "new_path": "b.jpg", "status": "planned"}],
    )

    path = write_manifest(manifest, tmp_path / "manifests")

    assert path.exists()
    assert manifest["dry_run"] is True
    assert manifest["files"][0]["status"] == "planned"


def test_undo_restores_file_from_manifest(tmp_path):
    original = tmp_path / "original.jpg"
    renamed = tmp_path / "renamed.jpg"
    renamed.write_text("photo", encoding="utf-8")
    manifest = create_manifest(
        input_directory=tmp_path,
        dry_run=False,
        provider_used=None,
        metadata_threshold=70,
        files=[{"original_path": str(original), "new_path": str(renamed), "status": "renamed"}],
    )
    manifest_path = write_manifest(manifest, tmp_path)

    results = undo_from_manifest(manifest_path)

    assert results[0]["path"] == str(original)
    assert results[0]["status"] == "restored"
    assert original.exists()
    assert not renamed.exists()


def test_undo_prevents_overwrite(tmp_path):
    original = tmp_path / "original.jpg"
    renamed = tmp_path / "renamed.jpg"
    original.write_text("original", encoding="utf-8")
    renamed.write_text("renamed", encoding="utf-8")
    manifest = create_manifest(
        input_directory=tmp_path,
        dry_run=False,
        provider_used=None,
        metadata_threshold=70,
        files=[{"original_path": str(original), "new_path": str(renamed), "status": "renamed"}],
    )
    manifest_path = write_manifest(manifest, tmp_path)

    results = undo_from_manifest(manifest_path)

    assert results[0]["path"] == str(original)
    assert results[0]["source"] == str(renamed)
    assert results[0]["status"] == "skipped_collision"
    assert renamed.exists()
