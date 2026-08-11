import pytest

from photosage.providers.base import build_provider_prompt
from photosage.providers.exceptions import InvalidResponseError
from photosage.providers.response_normalizer import normalize_response


def test_normalize_response_fills_missing_fields_and_clamps_confidence():
    response = normalize_response(
        '{"primary_subject": "Truck", "confidence": 1.8, "tags": "vehicle; outdoor"}',
        provider="openai",
        model="gpt-4.1-mini",
    )

    assert response["primary_subject"] == "Truck"
    assert response["secondary_subject"] == ""
    assert response["confidence"] == 1.0
    assert response["tags"] == ["outdoor", "vehicle"]
    assert response["provider"] == "openai"
    assert response["model"] == "gpt-4.1-mini"


def test_normalize_response_repairs_markdown_fence_and_trailing_comma():
    response = normalize_response(
        """```json
        {"primary_subject": "deck", "tags": ["construction",],}
        ```""",
        provider="anthropic",
        model="claude-sonnet-4",
    )

    assert response["primary_subject"] == "deck"
    assert response["tags"] == ["construction"]


def test_normalize_response_rejects_invalid_json():
    with pytest.raises(InvalidResponseError):
        normalize_response("not json", provider="gemini", model="gemini-2.5-pro")


def test_cloud_prompt_excludes_sensitive_metadata_by_default():
    prompt = build_provider_prompt(
        {
            "absolute_path": "C:/Private/Mick/photo.jpg",
            "original_filename": "private-name.jpg",
            "latitude": 36.5,
            "longitude": -87.8,
            "camera_model": "Camera",
        }
    )

    assert "Private" not in prompt
    assert "private-name" not in prompt
    assert "36.5" not in prompt
    assert "Camera" in prompt
