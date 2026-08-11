from PIL import Image

from photosage.config import AppConfig
from photosage.manifest.manifest_reader import load_manifest
from photosage.manifest.review import apply_review_decisions
from photosage.rename.renamer import preview_renames


def test_review_edits_and_approves_manifest(tmp_path):
    source = tmp_path / "IMG_001.jpg"
    Image.new("RGB", (12, 12)).save(source)
    config = AppConfig(manifest_directory=tmp_path / "manifests", metadata_threshold=0)
    result = preview_renames(tmp_path, config)

    reviewed = apply_review_decisions(
        result.manifest_path,
        [{"selector": "IMG_001.jpg", "action": "edit", "new_filename": "2026-01-01_test_photo_001.jpg"}],
        reviewer="test",
    )

    assert reviewed["files"][0]["new_filename"] == "2026-01-01_test_photo_001.jpg"
    assert reviewed["files"][0]["approval_status"] == "approved"
    assert reviewed["review_history"][0]["reviewer"] == "test"
    assert load_manifest(result.manifest_path)["manifest_sha256"] == reviewed["manifest_sha256"]
