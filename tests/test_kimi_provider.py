import json
import sys
from types import SimpleNamespace

import pytest
from PIL import Image

from photosage.providers.exceptions import AuthenticationError, InvalidResponseError, ProviderUnavailableError
from photosage.providers.kimi_provider import KIMI_BASE_URL, KimiProvider


def _response(content: str, finish_reason: str = "stop"):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content), finish_reason=finish_reason)])


def test_kimi_sends_private_json_vision_request(monkeypatch, tmp_path):
    image_path = tmp_path / "photo.jpg"
    Image.new("RGB", (8, 8), color="blue").save(image_path)
    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured["request"] = kwargs
            return _response(
                json.dumps(
                    {
                        "primary_subject": "lake",
                        "secondary_subject": "mountains",
                        "activity": "",
                        "environment": "outdoors",
                        "location_guess": "",
                        "confidence": 0.92,
                        "tags": ["water", "landscape"],
                        "description": "A lake below mountains.",
                    }
                )
            )

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setenv("MOONSHOT_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))
    provider = KimiProvider({"model": "kimi-k3", "reasoning_effort": "low"})

    result = provider.analyze_image(
        image_path,
        {"original_filename": "private-name.jpg", "latitude": 36.5, "camera_model": "Camera"},
    )

    assert captured["client"]["base_url"] == KIMI_BASE_URL
    request = captured["request"]
    assert request["model"] == "kimi-k3"
    assert request["response_format"] == {"type": "json_object"}
    assert request["reasoning_effort"] == "low"
    assert request["messages"][0]["content"][0]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    prompt = request["messages"][0]["content"][1]["text"]
    assert "private-name.jpg" not in prompt
    assert "36.5" not in prompt
    assert "Camera" in prompt
    assert result["provider"] == "kimi"
    assert result["primary_subject"] == "lake"


def test_kimi_requires_api_key(monkeypatch, tmp_path):
    monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)
    with pytest.raises(AuthenticationError, match="MOONSHOT_API_KEY"):
        KimiProvider().analyze_image(tmp_path / "photo.jpg", {})


def test_kimi_rejects_untrusted_base_url():
    with pytest.raises(ProviderUnavailableError, match="base_url"):
        KimiProvider({"base_url": "https://example.com/v1"})


def test_kimi_reports_truncated_json(monkeypatch, tmp_path):
    image_path = tmp_path / "photo.jpg"
    image_path.write_bytes(b"image")

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **request: _response('{"primary_subject":', "length")))

    monkeypatch.setenv("MOONSHOT_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))

    with pytest.raises(InvalidResponseError, match="truncated"):
        KimiProvider().analyze_image(image_path, {})


def test_kimi_k2_5_uses_supported_thinking_parameters(monkeypatch, tmp_path):
    image_path = tmp_path / "photo.jpg"
    image_path.write_bytes(b"image")
    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return _response('{"primary_subject":"photo","confidence":0.8}')

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setenv("MOONSHOT_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))

    KimiProvider({"model": "kimi-k2.5", "thinking": "disabled"}).analyze_image(image_path, {})

    assert captured["max_tokens"] == 1200
    assert captured["thinking"] == {"type": "disabled"}
    assert "temperature" not in captured
    assert "reasoning_effort" not in captured
