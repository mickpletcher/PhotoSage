import json

from photosage.manifest.manifest_writer import create_manifest, write_manifest
from photosage.manifest.undo import rollback_all


def test_rollback_collision_never_overwrites_original(tmp_path):
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

    result = rollback_all(manifest_path, report_directory=tmp_path / "reports")

    assert result.operations[0].status == "skipped_collision"
    assert original.read_text(encoding="utf-8") == "original"
    assert renamed.read_text(encoding="utf-8") == "renamed"


def test_rollback_report_contains_summary_and_operations(tmp_path):
    original = tmp_path / "original.jpg"
    renamed = tmp_path / "renamed.jpg"
    renamed.write_text("renamed", encoding="utf-8")
    manifest = create_manifest(
        input_directory=tmp_path,
        dry_run=False,
        provider_used=None,
        metadata_threshold=70,
        files=[{"original_path": str(original), "new_path": str(renamed), "status": "renamed"}],
    )
    manifest_path = write_manifest(manifest, tmp_path)

    result = rollback_all(manifest_path, report_directory=tmp_path / "reports")
    report = json.loads(result.report_path.read_text(encoding="utf-8"))

    assert report["summary"]["restored"] == 1
    assert report["operations"][0]["source"] == str(renamed)
    assert report["operations"][0]["destination"] == str(original)

