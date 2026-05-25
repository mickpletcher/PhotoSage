import json

from photosage.manifest.manifest_writer import create_manifest, write_manifest
from photosage.manifest.undo import rollback_all, undo_from_manifest
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
    assert results[1]["status"] == "skipped_missing"
    assert original.exists()


def test_rollback_skips_dry_run_manifest_items_as_failed_visibility(tmp_path):
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

    results = rollback_renames(manifest_path)

    assert results[0]["status"] == "failed"
    assert "not rollbackable" in results[0]["message"]


def test_dry_run_does_not_move_files_and_writes_report(tmp_path):
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

    result = rollback_all(manifest_path, dry_run=True, report_directory=tmp_path / "reports")

    assert result.summary["restored"] == 1
    assert renamed.exists()
    assert not original.exists()
    assert result.report_path.exists()
    report = json.loads(result.report_path.read_text(encoding="utf-8"))
    assert report["dry_run"] is True


def test_continue_on_error_false_stops_after_failure(tmp_path):
    first_original = tmp_path / "first-original.jpg"
    first_renamed = tmp_path / "first-renamed.jpg"
    second_original = tmp_path / "second-original.jpg"
    second_renamed = tmp_path / "second-renamed.jpg"
    first_original.write_text("collision", encoding="utf-8")
    first_renamed.write_text("renamed", encoding="utf-8")
    second_renamed.write_text("renamed", encoding="utf-8")
    manifest = create_manifest(
        input_directory=tmp_path,
        dry_run=False,
        provider_used=None,
        metadata_threshold=70,
        files=[
            {"original_path": str(first_original), "new_path": str(first_renamed), "status": "planned"},
            {"original_path": str(second_original), "new_path": str(second_renamed), "status": "renamed"},
        ],
    )
    manifest_path = write_manifest(manifest, tmp_path)

    result = rollback_all(manifest_path, continue_on_error=False, report_directory=tmp_path / "reports")

    assert len(result.operations) == 1
    assert result.operations[0].status == "failed"
    assert second_renamed.exists()


def test_undo_from_manifest_compatibility_wrapper(tmp_path):
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

    results = undo_from_manifest(manifest_path, report_directory=tmp_path / "reports")

    assert results[0]["status"] == "restored"
    assert results[0]["destination"] == str(original)

