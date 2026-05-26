from __future__ import annotations

from photosage.providers.base import VisionProvider
from photosage.providers.exceptions import (
    AuthenticationError,
    InvalidResponseError,
    ProviderError,
    ProviderUnavailableError,
    RetryLimitExceededError,
    UnsupportedModelError,
    UnsupportedProviderError,
)
from photosage.providers.healthcheck import ProviderHealth, check_lmstudio, check_ollama, check_providers, list_lmstudio_models, list_ollama_models, ollama_info
from photosage.providers.provider_factory import ProviderFactory
from photosage.providers.provider_manager import ProviderManager


def get_provider(name: str, settings: dict | None = None) -> VisionProvider:
    """Return a configured vision provider by name."""
    return ProviderFactory.create(name, settings=settings)


__all__ = [
    "AuthenticationError",
    "InvalidResponseError",
    "ProviderError",
    "ProviderFactory",
    "ProviderHealth",
    "ProviderManager",
    "ProviderUnavailableError",
    "RetryLimitExceededError",
    "UnsupportedModelError",
    "UnsupportedProviderError",
    "VisionProvider",
    "check_lmstudio",
    "check_ollama",
    "check_providers",
    "get_provider",
    "list_lmstudio_models",
    "list_ollama_models",
    "ollama_info",
]
