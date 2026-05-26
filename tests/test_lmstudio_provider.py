from pathlib import Path

import pytest
import requests
from PIL import Image

from photosage.providers.exceptions import InvalidResponseError, ProviderUnavailableError
from photosage.providers.lmstudio_provider import LMStudioProvider


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


def _image(path: Path) -> None:
    Image.new("RGB", (16, 16), (20, 30, 40)).save(path)


def test_lmstudio_provider_sends_openai_compatible_vision_payload(monkeypatch, tmp_path):
    image_path = tmp_path / "photo.jpg"
    _image(image_path)
    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"primary_subject":"nebula","confidence":0.8,"tags":["astro"],"description":"Deep sky image"}'
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("photosage.providers.lmstudio_provider.requests.post", fake_post)
    provider = LMStudioProvider({"endpoint": "http://localhost:1234/v1", "model": "qwen2.5-vl"})

    response = provider.analyze_image(image_path, {"original_filename": image_path.name})

    assert captured["url"] == "http://localhost:1234/v1/chat/completions"
    assert captured["json"]["model"] == "qwen2.5-vl"
    assert captured["json"]["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert response["provider"] == "lmstudio"
    assert response["primary_subject"] == "nebula"


def test_lmstudio_provider_retries_invalid_model_json(monkeypatch, tmp_path):
    image_path = tmp_path / "photo.jpg"
    _image(image_path)
    calls = {"count": 0}

    def fake_post(url, json, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            return FakeResponse({"choices": [{"message": {"content": "not json"}}]})
        return FakeResponse({"choices": [{"message": {"content": '{"primary_subject":"moon","confidence":0.7}'}}]})

    monkeypatch.setattr("photosage.providers.lmstudio_provider.requests.post", fake_post)
    provider = LMStudioProvider({"endpoint": "http://localhost:1234/v1", "model": "qwen2.5-vl"})

    response = provider.analyze_image(image_path, {})

    assert calls["count"] == 2
    assert response["primary_subject"] == "moon"


def test_lmstudio_provider_unreachable_endpoint(monkeypatch, tmp_path):
    image_path = tmp_path / "photo.jpg"
    _image(image_path)

    def fake_post(url, json, timeout):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr("photosage.providers.lmstudio_provider.requests.post", fake_post)
    provider = LMStudioProvider({"endpoint": "http://localhost:1234/v1", "model": "qwen2.5-vl"})

    with pytest.raises(ProviderUnavailableError):
        provider.analyze_image(image_path, {})


def test_lmstudio_provider_invalid_chat_envelope(monkeypatch, tmp_path):
    image_path = tmp_path / "photo.jpg"
    _image(image_path)
    monkeypatch.setattr("photosage.providers.lmstudio_provider.requests.post", lambda url, json, timeout: FakeResponse({"bad": []}))
    provider = LMStudioProvider({"endpoint": "http://localhost:1234/v1", "model": "qwen2.5-vl"})

    with pytest.raises(InvalidResponseError):
        provider.analyze_image(image_path, {})
