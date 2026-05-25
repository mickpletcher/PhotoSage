import requests
from PIL import Image

from photosage.providers.exceptions import InvalidResponseError, ProviderUnavailableError, UnsupportedModelError
from photosage.providers.ollama_provider import OllamaProvider


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


def _image(path):
    Image.new("RGB", (32, 24), color="red").save(path)


def test_ollama_provider_normalizes_valid_response(monkeypatch, tmp_path):
    photo = tmp_path / "photo.jpg"
    _image(photo)

    def fake_post(url, json, timeout):
        assert url == "http://localhost:11434/api/generate"
        assert json["model"] == "llava"
        assert json["images"]
        return FakeResponse(
            {
                "response": '{"primary_subject": "deck", "activity": "construction", "confidence": 0.8, "tags": ["build"]}'
            }
        )

    monkeypatch.setattr("photosage.providers.ollama_provider.requests.post", fake_post)

    response = OllamaProvider({"model": "llava"}).analyze_image(photo, {"original_filename": "photo.jpg"})

    assert response["provider"] == "ollama"
    assert response["model"] == "llava"
    assert response["primary_subject"] == "deck"
    assert response["confidence"] == 0.8


def test_ollama_provider_retries_once_after_malformed_response(monkeypatch, tmp_path):
    photo = tmp_path / "photo.jpg"
    _image(photo)
    calls = {"count": 0}

    def fake_post(url, json, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            return FakeResponse({"response": "not-json"})
        return FakeResponse({"response": '{"primary_subject": "container"}'})

    monkeypatch.setattr("photosage.providers.ollama_provider.requests.post", fake_post)

    response = OllamaProvider({"model": "llava"}).analyze_image(photo, {})

    assert calls["count"] == 2
    assert response["primary_subject"] == "container"


def test_ollama_provider_raises_after_second_malformed_response(monkeypatch, tmp_path):
    photo = tmp_path / "photo.jpg"
    _image(photo)
    monkeypatch.setattr("photosage.providers.ollama_provider.requests.post", lambda url, json, timeout: FakeResponse({"response": "bad"}))

    try:
        OllamaProvider({"model": "llava"}).analyze_image(photo, {})
    except InvalidResponseError:
        pass
    else:
        raise AssertionError("Expected InvalidResponseError")


def test_ollama_provider_timeout_is_provider_unavailable(monkeypatch, tmp_path):
    photo = tmp_path / "photo.jpg"
    _image(photo)

    def fake_post(url, json, timeout):
        raise requests.Timeout("slow")

    monkeypatch.setattr("photosage.providers.ollama_provider.requests.post", fake_post)

    try:
        OllamaProvider({"model": "llava"}).analyze_image(photo, {})
    except ProviderUnavailableError as error:
        assert "timed out" in str(error)
    else:
        raise AssertionError("Expected ProviderUnavailableError")


def test_ollama_provider_rejects_unsupported_model(tmp_path):
    photo = tmp_path / "photo.jpg"
    _image(photo)

    try:
        OllamaProvider({"model": "unsupported"}).analyze_image(photo, {})
    except UnsupportedModelError as error:
        assert "Unsupported Ollama model" in str(error)
    else:
        raise AssertionError("Expected UnsupportedModelError")

