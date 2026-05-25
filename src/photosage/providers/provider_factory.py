from __future__ import annotations

from typing import Any

from photosage.config import AppConfig
from photosage.providers.anthropic_provider import AnthropicProvider
from photosage.providers.base import VisionProvider
from photosage.providers.exceptions import UnsupportedProviderError
from photosage.providers.gemini_provider import GeminiProvider
from photosage.providers.ollama_provider import OllamaProvider
from photosage.providers.openai_provider import OpenAIProvider


class ProviderFactory:
    """Create configured vision providers."""

    PROVIDERS: dict[str, type[VisionProvider]] = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "ollama": OllamaProvider,
    }

    @classmethod
    def create(cls, name: str, config: AppConfig | None = None, settings: dict[str, Any] | None = None) -> VisionProvider:
        """Instantiate a provider by name."""
        provider_name = name.lower().strip()
        provider_class = cls.PROVIDERS.get(provider_name)
        if provider_class is None:
            raise UnsupportedProviderError(f"Unsupported vision provider: {name}")

        provider_settings = settings
        if provider_settings is None and config is not None:
            provider_settings = config.provider_settings.get(provider_name, {})
        return provider_class(settings=provider_settings or {})

