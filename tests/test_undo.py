from photosage.manifest.manifest_writer import create_manifest, write_manifest
from photosage.rename.renamer import rollback_renames


def test_rollback_renames_restores_partial_batch(tmp_path):
    original = tmp_path / "original.jpg"
    renamed = tmp_path / "renamed.jpg"
    missing = tmp_path / "missing-new.jpg"
    renamed.write_text("photo", encoding="utf-8")
    manifest = create_manifest(
        input_directory=tmp_path,
        dry_run=False,
        provider_used=None,
        metadata_threshold=70,
        files=[
            {"original_path": str(original), "new_path": str(renamed), "status": "renamed"},
            {"original_path": str(tmp_path / "missing-original.jpg"), "new_path": str(missing), "status": "renamed"},
        ],
    )
    manifest_path = write_manifest(manifest, tmp_path)

    results = rollback_renames(manifest_path)

    assert results[0]["status"] == "restored"
    assert results[1]["status"] == "missing"
    assert original.exists()


def test_rollback_skips_dry_run_manifest_items(tmp_path):
    original = tmp_path / "original.jpg"
    renamed = tmp_path / "renamed.jpg"
    manifest = create_manifest(
        input_directory=tmp_path,
        dry_run=True,
        provider_used=None,
        metadata_threshold=70,
        files=[{"original_path": str(original), "new_path": str(renamed), "status": "planned"}],
    )
    manifest_path = write_manifest(manifest, tmp_path)

    assert rollback_renames(manifest_path) == [{"path": str(renamed), "status": "not-applied"}]
