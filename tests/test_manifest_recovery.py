from PIL import Image

from photosage.config import AppConfig
from photosage.manifest.manifest_writer import write_manifest
from photosage.manifest.recovery import recover_manifest
from photosage.rename.renamer import preview_renames


def test_recovery_detects_completed_interrupted_move(tmp_path):
    source = tmp_path / "IMG_001.jpg"
    Image.new("RGB", (12, 12)).save(source)
    result = preview_renames(tmp_path, AppConfig(manifest_directory=tmp_path / "manifests", metadata_threshold=0))
    item = result.manifest["files"][0]
    destination = item["new_path"]
    source.rename(destination)
    item["status"] = "rename-started"
    write_manifest(result.manifest, result.manifest_path.parent, result.manifest_path)

    inspected = recover_manifest(result.manifest_path)
    resumed = recover_manifest(result.manifest_path, action="resume")

    assert inspected["operations"][0]["recovery_state"] == "completed"
    assert resumed["operations"][0]["recovery_state"] == "completed"
