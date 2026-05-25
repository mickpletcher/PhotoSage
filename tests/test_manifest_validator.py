import json

from photosage.manifest.manifest_writer import create_manifest, write_manifest
from photosage.manifest.validator import validate_manifest_integrity


def test_manifest_validator_passes_valid_renamed_manifest(tmp_path):
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

    report = validate_manifest_integrity(manifest_path)

    assert report.valid is True
    assert report.summary["errors"] == 0


def test_manifest_validator_reports_missing_renamed_file(tmp_path):
    manifest = create_manifest(
        input_directory=tmp_path,
        dry_run=False,
        provider_used=None,
        metadata_threshold=70,
        files=[{"original_path": str(tmp_path / "original.jpg"), "new_path": str(tmp_path / "missing.jpg"), "status": "renamed"}],
    )
    manifest_path = write_manifest(manifest, tmp_path)

    report = validate_manifest_integrity(manifest_path)

    assert report.valid is False
    assert report.issues[0].code == "missing_renamed_file"


def test_manifest_validator_reports_sidecar_mismatch(tmp_path):
    renamed = tmp_path / "renamed.jpg"
    renamed.write_text("photo", encoding="utf-8")
    manifest = create_manifest(
        input_directory=tmp_path,
        dry_run=False,
        provider_used=None,
        metadata_threshold=70,
        files=[
            {
                "original_path": str(tmp_path / "original.jpg"),
                "new_path": str(renamed),
                "status": "renamed",
                "xmp_detected": True,
                "xmp_path": str(tmp_path / "original.xmp"),
                "new_xmp_path": str(tmp_path / "renamed.xmp"),
                "sidecar_status": "renamed",
            }
        ],
    )
    manifest_path = write_manifest(manifest, tmp_path)

    report = validate_manifest_integrity(manifest_path)

    assert report.valid is False
    assert any(issue.code == "missing_sidecar" for issue in report.issues)


def test_manifest_validator_hashes_existing_files(tmp_path):
    renamed = tmp_path / "renamed.jpg"
    renamed.write_text("photo", encoding="utf-8")
    manifest = create_manifest(
        input_directory=tmp_path,
        dry_run=False,
        provider_used=None,
        metadata_threshold=70,
        files=[{"original_path": str(tmp_path / "original.jpg"), "new_path": str(renamed), "status": "renamed"}],
    )
    manifest_path = write_manifest(manifest, tmp_path)

    report = validate_manifest_integrity(manifest_path, include_hashes=True)

    assert str(renamed) in report.hashes
    assert len(report.hashes[str(renamed)]) == 64


def test_manifest_validator_reports_malformed_manifest(tmp_path):
    manifest_path = tmp_path / "bad.json"
    manifest_path.write_text(json.dumps({"files": []}), encoding="utf-8")

    report = validate_manifest_integrity(manifest_path)

    assert report.valid is False
    assert report.issues[0].code == "malformed_manifest"
