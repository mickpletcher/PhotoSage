import json

from PIL import Image
from typer.testing import CliRunner

from photosage.cli import app
from photosage.config import AppConfig
from photosage.lightroom.exporter import process_lightroom_export
from photosage.manifest.undo import rollback_all


runner = CliRunner()


def _write_image(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), color="blue").save(path)


def _write_xmp(path):
    path.write_text(
        """<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:xmp="http://ns.adobe.com/xap/1.0/">
    <rdf:Description xmp:Rating="4">
      <dc:title><rdf:Alt><rdf:li xml:lang="x-default">Container Home</rdf:li></rdf:Alt></dc:title>
      <dc:subject><rdf:Bag><rdf:li>construction</rdf:li></rdf:Bag></dc:subject>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>""",
        encoding="utf-8",
    )


def test_lightroom_preview_writes_manifest_without_renaming_sidecar(tmp_path):
    photo = tmp_path / "exports" / "IMG_0001.jpg"
    _write_image(photo)
    _write_xmp(photo.with_suffix(".xmp"))
    config = AppConfig(manifest_directory=tmp_path / "manifests")

    result = process_lightroom_export(photo.parent, config, preview=True, apply=False)

    assert photo.exists()
    assert photo.with_suffix(".xmp").exists()
    assert result.manifest_path.exists()
    assert result.manifest["lightroom_mode"] is True
    assert result.manifest["files"][0]["xmp_detected"] is True
    assert result.manifest["files"][0]["status"] == "planned"


def test_lightroom_apply_renames_image_and_matching_sidecar(tmp_path):
    photo = tmp_path / "exports" / "IMG_0001.jpg"
    _write_image(photo)
    _write_xmp(photo.with_suffix(".xmp"))
    config = AppConfig(manifest_directory=tmp_path / "manifests")

    result = process_lightroom_export(photo.parent, config, preview=False, apply=True)
    item = result.manifest["files"][0]
    new_photo = tmp_path / "exports" / item["new_filename"]
    new_sidecar = new_photo.with_suffix(".xmp")

    assert item["status"] == "renamed"
    assert item["sidecar_status"] == "renamed"
    assert not photo.exists()
    assert not photo.with_suffix(".xmp").exists()
    assert new_photo.exists()
    assert new_sidecar.exists()
    saved = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert saved["files"][0]["sidecar_status"] == "renamed"


def test_lightroom_manifest_undo_restores_image_and_sidecar(tmp_path):
    photo = tmp_path / "exports" / "IMG_0001.jpg"
    sidecar = photo.with_suffix(".xmp")
    _write_image(photo)
    _write_xmp(sidecar)
    config = AppConfig(manifest_directory=tmp_path / "manifests")

    result = process_lightroom_export(photo.parent, config, preview=False, apply=True)
    rollback = rollback_all(result.manifest_path, report_directory=tmp_path / "rollback_reports")

    assert rollback.summary["restored"] == 2
    assert photo.exists()
    assert sidecar.exists()


def test_cli_lightroom_process_preview_outputs_json(tmp_path):
    photo = tmp_path / "exports" / "IMG_0001.jpg"
    output = tmp_path / "lightroom.json"
    config = tmp_path / "config.yaml"
    _write_image(photo)
    _write_xmp(photo.with_suffix(".xmp"))
    config.write_text(
        f"""
metadata_threshold: 0
manifest_directory: {(tmp_path / "manifests").as_posix()}
log_file: {(tmp_path / "logs" / "photosage.log").as_posix()}
filename_format: "{{date}}_{{location}}_{{subject}}_{{context}}_{{counter}}"
""".strip(),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["lightroom-process", "--input", str(photo.parent), "--preview", "--output-json", str(output), "--config", str(config)],
    )

    assert result.exit_code == 0
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["lightroom_mode"] is True
    assert data["files"][0]["xmp_detected"] is True
