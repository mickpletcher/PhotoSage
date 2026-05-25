import json

from PIL import Image

from photosage.config import AppConfig
from photosage.providers.exceptions import AuthenticationError
from photosage.providers.provider_manager import ProviderManager
from photosage.rename.renamer import apply_renames, preview_renames


def _write_image(path):
    Image.new("RGB", (10, 10), color="red").save(path)


def test_preview_renames_writes_manifest_without_renaming(tmp_path):
    photo = tmp_path / "Shipping Container.JPG"
    _write_image(photo)
    config = AppConfig(manifest_directory=tmp_path / "manifests", metadata_threshold=70)

    result = preview_renames(tmp_path, config)

    assert photo.exists()
    assert result.manifest_path.exists()
    assert result.manifest["dry_run"] is True
    assert result.manifest["files"][0]["status"] == "planned"
    assert result.manifest["files"][0]["new_filename"].endswith("_001.jpg")


def test_apply_renames_moves_file_and_updates_manifest(tmp_path):
    photo = tmp_path / "IMG_0001.jpg"
    _write_image(photo)
    config = AppConfig(manifest_directory=tmp_path / "manifests", metadata_threshold=70)
    ai_responses = {
        photo.name: {
            "primary_subject": "Shipping Container",
            "activity": "Deck Construction",
            "location_guess": "Dover TN",
            "provider": "test",
        }
    }

    result = apply_renames(tmp_path, config, ai_responses=ai_responses)
    item = result.manifest["files"][0]

    assert item["status"] == "renamed"
    assert not photo.exists()
    assert (tmp_path / item["new_filename"]).exists()
    saved = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert saved["files"][0]["status"] == "renamed"


def test_apply_renames_prevents_collision_with_existing_file(tmp_path):
    source = tmp_path / "IMG_0001.jpg"
    existing = tmp_path / "2026-05-20_dover-tn_deck_build_001.jpg"
    _write_image(source)
    _write_image(existing)
    config = AppConfig(
        manifest_directory=tmp_path / "manifests",
        filename_format="{date}_{location}_{subject}_{context}_{counter}",
    )
    ai_responses = {
        source.name: {
            "primary_subject": "Deck",
            "activity": "Build",
            "location_guess": "Dover TN",
        }
    }

    result = apply_renames(tmp_path, config, ai_responses=ai_responses)
    filenames = {item["new_filename"] for item in result.manifest["files"]}

    assert len(filenames) == 2
    assert all((tmp_path / filename).exists() for filename in filenames)


def test_preview_renames_runs_live_ai_when_metadata_is_below_threshold(monkeypatch, tmp_path):
    photo = tmp_path / "IMG_0001.jpg"
    _write_image(photo)
    config = AppConfig(manifest_directory=tmp_path / "manifests", metadata_threshold=100)

    def fake_analyze(self, image_path, metadata):
        return {
            "primary_subject": "Shipping Container",
            "activity": "Deck Construction",
            "location_guess": "Dover TN",
            "confidence": 0.9,
            "provider": "anthropic",
            "model": "claude-test",
        }

    monkeypatch.setattr(ProviderManager, "analyze_image", fake_analyze)

    result = preview_renames(tmp_path, config, analyze_ai=True)
    item = result.manifest["files"][0]

    assert item["ai_required"] is True
    assert item["ai_used"] is True
    assert item["ai_response"]["provider"] == "anthropic"
    assert "shipping-container" in item["new_filename"]
    assert result.manifest["provider_used"] == "anthropic"


def test_apply_renames_skips_when_required_ai_is_unavailable(monkeypatch, tmp_path):
    photo = tmp_path / "IMG_0001.jpg"
    _write_image(photo)
    config = AppConfig(manifest_directory=tmp_path / "manifests", metadata_threshold=100)

    def fake_analyze(self, image_path, metadata):
        raise AuthenticationError("missing key")

    monkeypatch.setattr(ProviderManager, "analyze_image", fake_analyze)

    result = apply_renames(tmp_path, config, analyze_ai=True)
    item = result.manifest["files"][0]

    assert item["status"] == "ai-unavailable"
    assert item["ai_used"] is False
    assert "AuthenticationError" in item["ai_error"]
    assert photo.exists()
