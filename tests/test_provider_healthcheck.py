import requests

from photosage.config import AppConfig
from photosage.providers.healthcheck import (
    check_lmstudio,
    check_ollama,
    check_providers,
    list_lmstudio_models,
    list_ollama_models,
    ollama_info,
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


def test_list_ollama_models_reads_api_tags(monkeypatch):
    monkeypatch.setattr(
        "photosage.providers.healthcheck.requests.get",
        lambda url, timeout, **kwargs: FakeResponse({"models": [{"name": "llava:13b"}, {"name": "bakllava"}]}),
    )

    assert list_ollama_models("http://localhost:11434") == ["bakllava", "llava:13b"]


def test_list_lmstudio_models_reads_openai_models(monkeypatch):
    monkeypatch.setattr(
        "photosage.providers.healthcheck.requests.get",
        lambda url, timeout, **kwargs: FakeResponse({"data": [{"id": "qwen2.5-vl"}, {"id": "llava"}]}),
    )

    assert list_lmstudio_models("http://localhost:1234/v1") == ["llava", "qwen2.5-vl"]


def test_check_ollama_reports_missing_model(monkeypatch):
    monkeypatch.setattr(
        "photosage.providers.healthcheck.requests.get",
        lambda url, timeout, **kwargs: FakeResponse({"models": [{"name": "llava"}]}),
    )
    config = AppConfig(provider_settings={"ollama": {"model": "llava:13b", "endpoint": "http://localhost:11434"}})

    health = check_ollama(config)

    assert health.status == "ERROR"
    assert "ollama pull llava:13b" in health.message


def test_check_ollama_reports_available_model(monkeypatch):
    monkeypatch.setattr(
        "photosage.providers.healthcheck.requests.get",
        lambda url, timeout, **kwargs: FakeResponse({"models": [{"name": "llava:13b"}]}),
    )
    config = AppConfig(provider_settings={"ollama": {"model": "llava:13b", "endpoint": "http://localhost:11434"}})

    health = check_ollama(config)

    assert health.status == "OK"
    assert health.model == "llava:13b"


def test_check_lmstudio_reports_available_model(monkeypatch):
    monkeypatch.setattr(
        "photosage.providers.healthcheck.requests.get",
        lambda url, timeout, **kwargs: FakeResponse({"data": [{"id": "qwen2.5-vl"}]}),
    )
    config = AppConfig(provider_settings={"lmstudio": {"model": "qwen2.5-vl", "endpoint": "http://localhost:1234/v1"}})

    health = check_lmstudio(config)

    assert health.status == "OK"
    assert health.model == "qwen2.5-vl"


def test_check_lmstudio_reports_missing_model(monkeypatch):
    monkeypatch.setattr(
        "photosage.providers.healthcheck.requests.get",
        lambda url, timeout, **kwargs: FakeResponse({"data": [{"id": "llava"}]}),
    )
    config = AppConfig(provider_settings={"lmstudio": {"model": "qwen2.5-vl", "endpoint": "http://localhost:1234/v1"}})

    health = check_lmstudio(config)

    assert health.status == "ERROR"
    assert "not loaded" in health.message


def test_check_providers_disables_cloud_when_local_only(monkeypatch):
    monkeypatch.setattr(
        "photosage.providers.healthcheck.requests.get",
        lambda url, timeout, **kwargs: FakeResponse({"models": [{"name": "llava"}]}),
    )
    config = AppConfig(local_only=True, provider_settings={"ollama": {"model": "llava"}})

    statuses = {health.name: health.status for health in check_providers(config)}

    assert statuses["ollama"] == "OK"
    assert statuses["lmstudio"] == "ERROR"
    assert statuses["anthropic"] == "DISABLED"
    assert statuses["openai"] == "DISABLED"
    assert statuses["gemini"] == "DISABLED"
    assert statuses["kimi"] == "DISABLED"


def test_check_providers_reports_configured_kimi_without_api_call(monkeypatch):
    monkeypatch.setattr(
        "photosage.providers.healthcheck.requests.get",
        lambda url, timeout, **kwargs: FakeResponse({"models": [] if url.endswith("/models") else [{"name": "llava"}]}),
    )
    monkeypatch.setattr("photosage.providers.healthcheck._module_available", lambda name: True)
    monkeypatch.setenv("MOONSHOT_API_KEY", "test-key")
    config = AppConfig(local_only=False, provider_settings={"kimi": {"model": "kimi-k3"}})

    health = next(item for item in check_providers(config) if item.name == "kimi")

    assert health.status == "CONFIGURED"
    assert health.model == "kimi-k3"
    assert health.endpoint == "https://api.moonshot.ai/v1"


def test_ollama_info_best_effort(monkeypatch):
    def fake_get(url, timeout, **kwargs):
        if url.endswith("/api/version"):
            return FakeResponse({"version": "0.1.0"})
        return FakeResponse({"models": [{"name": "llava"}]})

    monkeypatch.setattr("photosage.providers.healthcheck.requests.get", fake_get)

    info = ollama_info("http://localhost:11434")

    assert info["version"] == "0.1.0"
    assert info["models"] == ["llava"]
    assert info["inference_mode"] == "local"
