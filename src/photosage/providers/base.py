from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from photosage.providers.response_normalizer import empty_response, normalize_response

LOCAL_PROVIDERS = {"ollama"}
CLOUD_PROVIDERS = {"anthropic", "openai", "gemini"}


class VisionProvider(ABC):
    """Base class for image understanding providers."""

    provider_name = "base"
    default_model = ""
    is_local = False

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self.settings = settings or {}
        self.model = str(self.settings.get("model") or self.default_model)

    @abstractmethod
    def analyze_image(self, image_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        """Analyze image content and return normalized structured JSON."""

    def normalize(self, payload: str | dict[str, Any]) -> dict[str, Any]:
        """Normalize provider payload into the shared contract."""
        return normalize_response(payload, provider=self.provider_name, model=self.model)

    def stub_response(self, image_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        """Return deterministic structured data without remote analysis."""
        response = empty_response(provider=self.provider_name, model=self.model)
        response.update(
            {
                "primary_subject": image_path.stem,
                "confidence": 0.1,
                "tags": ["unverified"],
                "description": "Provider client is not configured. No remote image analysis was performed.",
            }
        )
        return self.normalize(response)

    def image_as_base64(self, image_path: Path) -> str:
        """Encode an image as base64 for provider APIs."""
        return base64.b64encode(image_path.read_bytes()).decode("ascii")


def _prompt_template() -> str:
    prompt_path = Path("prompts/image_classification.md")
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return "Classify image content for a photo organization tool. Return JSON only."


def build_provider_prompt(metadata: dict[str, Any]) -> str:
    """Build a provider prompt that asks only for factual classification JSON."""
    safe_metadata = {
        key: value
        for key, value in metadata.items()
        if key not in {"raw_metadata"} and value not in (None, "", [], {})
    }
    return (
        f"{_prompt_template()}\n\n"
        "Return JSON only. Do not rename the file. Do not output markdown. "
        "Do not identify private people unless names already exist in metadata. "
        "Avoid speculation, emotional descriptions, and assumptions. "
        "Use concise factual labels. "
        "Schema: primary_subject, secondary_subject, activity, environment, "
        "location_guess, confidence, tags, description. "
        f"Metadata: {safe_metadata}"
    )
