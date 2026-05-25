from pathlib import Path

from photosage.config import AppConfig
from photosage.providers.base import VisionProvider
from photosage.providers.exceptions import ProviderUnavailableError
from photosage.providers.provider_factory import ProviderFactory
from photosage.providers.provider_manager import ProviderManager
from photosage.providers.retry_handler import RetryConfig


class FailingProvider(VisionProvider):
    provider_name = "anthropic"
    default_model = "failing"

    def analyze_image(self, image_path: Path, metadata: dict) -> dict:
        raise ProviderUnavailableError("down")


class WorkingProvider(VisionProvider):
    provider_name = "openai"
    default_model = "working"

    def analyze_image(self, image_path: Path, metadata: dict) -> dict:
        return self.normalize({"primary_subject": "container", "confidence": 0.7})


def test_provider_manager_falls_back_to_next_provider(monkeypatch, tmp_path):
    providers = {"anthropic": FailingProvider, "openai": WorkingProvider}
    monkeypatch.setattr(ProviderFactory, "PROVIDERS", providers)
    config = AppConfig(vision_provider="anthropic", fallback_order=["openai"], provider_retry_count=1)
    manager = ProviderManager(config, RetryConfig(attempts=1, initial_delay_seconds=0))

    response = manager.analyze_image(tmp_path / "photo.jpg", {})

    assert response["provider"] == "openai"
    assert response["primary_subject"] == "container"


def test_provider_manager_raises_when_all_providers_fail(monkeypatch, tmp_path):
    monkeypatch.setattr(ProviderFactory, "PROVIDERS", {"anthropic": FailingProvider})
    config = AppConfig(vision_provider="anthropic", fallback_order=[], provider_retry_count=1)
    manager = ProviderManager(config, RetryConfig(attempts=1, initial_delay_seconds=0))

    try:
        manager.analyze_image(tmp_path / "photo.jpg", {})
    except ProviderUnavailableError as error:
        assert "No provider succeeded" in str(error)
    else:
        raise AssertionError("Expected ProviderUnavailableError")

