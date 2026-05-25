from pathlib import Path

from photosage.config import AppConfig
from photosage.providers.base import VisionProvider
from photosage.providers.provider_factory import ProviderFactory
from photosage.providers.provider_manager import ProviderManager
from photosage.providers.retry_handler import RetryConfig


class CloudProvider(VisionProvider):
    provider_name = "anthropic"
    default_model = "cloud"

    def analyze_image(self, image_path: Path, metadata: dict) -> dict:
        raise AssertionError("cloud provider should be blocked in local_only mode")


class LocalProvider(VisionProvider):
    provider_name = "ollama"
    default_model = "llava"
    is_local = True

    def analyze_image(self, image_path: Path, metadata: dict) -> dict:
        return self.normalize({"primary_subject": "local", "confidence": 0.6})


class LocalStudioProvider(VisionProvider):
    provider_name = "lmstudio"
    default_model = "local"
    is_local = True

    def analyze_image(self, image_path: Path, metadata: dict) -> dict:
        return self.normalize({"primary_subject": "studio", "confidence": 0.6})


def test_local_only_mode_filters_cloud_providers(monkeypatch, tmp_path):
    monkeypatch.setattr(ProviderFactory, "PROVIDERS", {"anthropic": CloudProvider, "ollama": LocalProvider})
    config = AppConfig(
        vision_provider="anthropic",
        fallback_order=["anthropic", "openai", "gemini", "ollama"],
        local_only=True,
    )
    manager = ProviderManager(config, RetryConfig(attempts=1, initial_delay_seconds=0))

    response = manager.analyze_image(tmp_path / "photo.jpg", {})

    assert manager.provider_order() == ["ollama"]
    assert response["provider"] == "ollama"
    assert response["primary_subject"] == "local"


def test_local_only_mode_allows_registered_local_providers(monkeypatch, tmp_path):
    monkeypatch.setattr(
        ProviderFactory,
        "PROVIDERS",
        {"anthropic": CloudProvider, "lmstudio": LocalStudioProvider, "ollama": LocalProvider},
    )
    config = AppConfig(
        vision_provider="lmstudio",
        fallback_order=["anthropic", "ollama"],
        local_only=True,
    )
    manager = ProviderManager(config, RetryConfig(attempts=1, initial_delay_seconds=0))

    response = manager.analyze_image(tmp_path / "photo.jpg", {})

    assert manager.provider_order() == ["lmstudio", "ollama"]
    assert response["provider"] == "lmstudio"
    assert response["primary_subject"] == "studio"
