import json
from pathlib import Path

from PIL import Image
from typer.testing import CliRunner

from photosage.cli import app
from photosage.manifest.manifest_writer import create_manifest, write_manifest

runner = CliRunner()


def _write_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest_directory = (path.parent / "manifests").as_posix()
    log_file = (path.parent / "logs" / "photosage.log").as_posix()
    path.write_text(
        f"""
vision_provider: anthropic
metadata_threshold: 70
manifest_directory: {manifest_directory}
log_file: {log_file}
fallback_order:
  - anthropic
  - openai
  - gemini
  - ollama
filename_format: "{{date}}_{{location}}_{{subject}}_{{context}}_{{counter}}"
""".strip(),
        encoding="utf-8",
    )


def _write_image(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), color="red").save(path)


def test_cli_scan_outputs_json_and_provider_override(tmp_path):
    config = tmp_path / "config.yaml"
    output = tmp_path / "scan.json"
    _write_config(config)
    _write_image(tmp_path / "photos" / "IMG_0001.jpg")
    (tmp_path / "photos" / "notes.txt").write_text("skip", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "scan",
            "--input",
            str(tmp_path / "photos"),
            "--provider",
            "ollama",
            "--local-only",
            "--output-json",
            str(output),
            "--config",
            str(config),
        ],
    )

    assert result.exit_code == 0
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["summary"]["provider_selected"] == "ollama"
    assert data["summary"]["supported_files"] == 1
    assert data["summary"]["unsupported_files"] == 1


def test_cli_preview_generates_json_without_renaming(tmp_path):
    config = tmp_path / "config.yaml"
    output = tmp_path / "preview.json"
    photo = tmp_path / "photos" / "IMG_0001.jpg"
    _write_config(config)
    _write_image(photo)

    result = runner.invoke(app, ["preview", "--input", str(photo.parent), "--output-json", str(output), "--config", str(config)])

    assert result.exit_code == 0
    assert photo.exists()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["dry_run"] is True
    assert data["files"][0]["status"] == "planned"


def test_cli_rename_requires_apply(tmp_path):
    config = tmp_path / "config.yaml"
    photo = tmp_path / "photos" / "IMG_0001.jpg"
    _write_config(config)
    _write_image(photo)

    result = runner.invoke(app, ["rename", "--input", str(photo.parent), "--config", str(config)])

    assert result.exit_code == 0
    assert "No files were renamed" in result.stdout
    assert photo.exists()


def test_cli_rename_apply_and_undo_force(tmp_path):
    config = tmp_path / "config.yaml"
    output = tmp_path / "rename.json"
    undo_output = tmp_path / "undo.json"
    photo = tmp_path / "photos" / "IMG_0001.jpg"
    _write_config(config)
    _write_image(photo)

    rename_result = runner.invoke(
        app,
        ["rename", "--input", str(photo.parent), "--apply", "--output-json", str(output), "--config", str(config)],
    )
    rename_data = json.loads(output.read_text(encoding="utf-8"))
    written_manifest = sorted((tmp_path / "manifests").glob("rename_manifest_*.json"))[-1]

    undo_result = runner.invoke(
        app,
        ["undo", "--manifest", str(written_manifest), "--force", "--output-json", str(undo_output), "--config", str(config)],
    )

    assert rename_result.exit_code == 0
    assert undo_result.exit_code == 0
    assert photo.exists()
    assert rename_data["files"][0]["status"] == "renamed"
    undo_data = json.loads(undo_output.read_text(encoding="utf-8"))
    assert undo_data["summary"]["restored"] == 1


def test_cli_invalid_provider_fails(tmp_path):
    config = tmp_path / "config.yaml"
    _write_config(config)
    _write_image(tmp_path / "photos" / "IMG_0001.jpg")

    result = runner.invoke(app, ["scan", "--input", str(tmp_path / "photos"), "--provider", "bad", "--config", str(config)])

    assert result.exit_code != 0


def test_cli_undo_dry_run_does_not_move(tmp_path):
    config = tmp_path / "config.yaml"
    _write_config(config)
    original = tmp_path / "photos" / "original.jpg"
    renamed = tmp_path / "photos" / "renamed.jpg"
    renamed.parent.mkdir(parents=True)
    renamed.write_text("photo", encoding="utf-8")
    manifest = create_manifest(
        input_directory=renamed.parent,
        dry_run=False,
        provider_used=None,
        metadata_threshold=70,
        files=[{"original_path": str(original), "new_path": str(renamed), "status": "renamed"}],
    )
    manifest_path = write_manifest(manifest, tmp_path)

    result = runner.invoke(app, ["undo", "--manifest", str(manifest_path), "--dry-run", "--config", str(config)])

    assert result.exit_code == 0
    assert renamed.exists()
    assert not original.exists()


def test_cli_manifest_validate_outputs_json(tmp_path):
    config = tmp_path / "config.yaml"
    output = tmp_path / "manifest-validation.json"
    _write_config(config)
    original = tmp_path / "photos" / "original.jpg"
    renamed = tmp_path / "photos" / "renamed.jpg"
    renamed.parent.mkdir(parents=True)
    renamed.write_text("photo", encoding="utf-8")
    manifest = create_manifest(
        input_directory=renamed.parent,
        dry_run=False,
        provider_used=None,
        metadata_threshold=70,
        files=[{"original_path": str(original), "new_path": str(renamed), "status": "renamed"}],
    )
    manifest_path = write_manifest(manifest, tmp_path)

    result = runner.invoke(
        app,
        ["manifest", "validate", "--manifest", str(manifest_path), "--output-json", str(output), "--config", str(config)],
    )

    assert result.exit_code == 0
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["valid"] is True
    assert data["summary"]["files"] == 1


def test_cli_ollama_models_lists_installed_models(monkeypatch, tmp_path):
    config = tmp_path / "config.yaml"
    _write_config(config)
    monkeypatch.setattr("photosage.cli.list_ollama_models", lambda endpoint, timeout_seconds: ["llava", "llava:13b"])

    result = runner.invoke(app, ["ollama", "models", "--config", str(config)])

    assert result.exit_code == 0
    assert "llava:13b" in result.stdout


def test_cli_providers_displays_health(monkeypatch, tmp_path):
    config = tmp_path / "config.yaml"
    _write_config(config)
    monkeypatch.setattr(
        "photosage.cli.check_providers",
        lambda cli_config: [
            type("Health", (), {"status": "OK", "name": "ollama", "model": "llava", "endpoint": "http://localhost:11434", "message": "ok"})()
        ],
    )

    result = runner.invoke(app, ["providers", "--config", str(config)])

    assert result.exit_code == 0
    assert "ollama" in result.stdout
