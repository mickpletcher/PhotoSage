import pytest

from photosage.config import AppConfig
from photosage.providers.anthropic_provider import AnthropicProvider
from photosage.providers.exceptions import UnsupportedProviderError
from photosage.providers.lmstudio_provider import LMStudioProvider
from photosage.providers.ollama_provider import OllamaProvider
from photosage.providers.provider_factory import ProviderFactory


def test_provider_factory_creates_configured_provider():
    config = AppConfig(provider_settings={"anthropic": {"model": "claude-test"}})

    provider = ProviderFactory.create("anthropic", config)

    assert isinstance(provider, AnthropicProvider)
    assert provider.model == "claude-test"


def test_provider_factory_creates_ollama_with_endpoint():
    config = AppConfig(provider_settings={"ollama": {"model": "llava", "endpoint": "http://localhost:11434"}})

    provider = ProviderFactory.create("ollama", config)

    assert isinstance(provider, OllamaProvider)
    assert provider.is_local is True
    assert provider.endpoint == "http://localhost:11434"


def test_provider_factory_creates_lmstudio_with_endpoint():
    config = AppConfig(provider_settings={"lmstudio": {"model": "qwen2.5-vl", "endpoint": "http://localhost:1234/v1"}})

    provider = ProviderFactory.create("lmstudio", config)

    assert isinstance(provider, LMStudioProvider)
    assert provider.is_local is True
    assert provider.endpoint == "http://localhost:1234/v1"
    assert provider.model == "qwen2.5-vl"


def test_provider_factory_rejects_unsupported_provider():
    with pytest.raises(UnsupportedProviderError):
        ProviderFactory.create("bad-provider")
