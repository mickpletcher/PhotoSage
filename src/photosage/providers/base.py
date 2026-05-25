from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

AI_SCHEMA_KEYS = {
    "primary_subject",
    "secondary_subject",
    "activity",
    "environment",
    "location_guess",
    "confidence",
    "tags",
    "description",
}


class VisionProvider(ABC):
    """Base class for vision providers."""

    name = "base"

    @abstractmethod
    def analyze_image(self, image_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        """Analyze an image and return normalized structured image understanding data."""


def empty_ai_response() -> dict[str, Any]:
    """Return the normalized JSON contract with empty values."""
    return {
        "primary_subject": "",
        "secondary_subject": "",
        "activity": "",
        "environment": "",
        "location_guess": "",
        "confidence": 0.0,
        "tags": [],
        "description": "",
    }


def validate_ai_response(response: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize provider response data."""
    missing = AI_SCHEMA_KEYS.difference(response)
    if missing:
        raise ValueError(f"AI response missing keys: {sorted(missing)}")

    normalized = empty_ai_response()
    normalized.update(response)
    normalized["confidence"] = float(normalized["confidence"])
    normalized["tags"] = [str(tag) for tag in (normalized.get("tags") or [])]
    return normalized


class StubVisionProvider(VisionProvider):
    """Provider stub that does not upload image data."""

    name = "stub"

    def analyze_image(self, image_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        """Return low confidence structured data without remote analysis."""
        response = empty_ai_response()
        response.update(
            {
                "primary_subject": image_path.stem,
                "confidence": 0.1,
                "tags": ["unverified"],
                "description": "Provider stub returned no remote analysis.",
            }
        )
        return validate_ai_response(response)

