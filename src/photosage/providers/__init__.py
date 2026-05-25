from __future__ import annotations

from photosage.providers.anthropic_provider import AnthropicProvider
from photosage.providers.base import VisionProvider
from photosage.providers.gemini_provider import GeminiProvider
from photosage.providers.ollama_provider import OllamaProvider
from photosage.providers.openai_provider import OpenAIProvider


def get_provider(name: str) -> VisionProvider:
    """Return a configured vision provider by name."""
    providers: dict[str, type[VisionProvider]] = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "ollama": OllamaProvider,
    }
    provider_class = providers.get(name.lower())
    if provider_class is None:
        raise ValueError(f"Unsupported vision provider: {name}")
    return provider_class()

