from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from importlib.resources import files
from pathlib import Path
from typing import Any

from photosage.providers.response_normalizer import empty_response, normalize_response

LOCAL_PROVIDERS = {"ollama", "lmstudio", "openai_compatible_local"}
CLOUD_PROVIDERS = {"anthropic", "openai", "gemini", "kimi"}
SAFE_CLOUD_METADATA_FIELDS = {
    "extension",
    "file_extension",
    "file_size",
    "width",
    "height",
    "image_width",
    "image_height",
    "orientation",
    "color_mode",
    "camera_make",
    "camera_model",
    "lens_model",
    "focal_length",
    "iso",
    "shutter_speed",
    "aperture",
    "exposure_program",
    "media_type",
    "content_label",
    "document_type",
    "astro_mode",
    "astro_profile",
    "astro_telescope",
    "astro_filter",
    "astro_exposure",
    "fits_detected",
    "duration_seconds",
    "codec",
    "frame_rate",
}


class VisionProvider(ABC):
    """Base class for image understanding providers."""

    provider_name = "base"
    default_model = ""
    is_local = False

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self.settings = settings or {}
        self.model = str(self.settings.get("model") or self.default_model)
        self.endpoint_trust = "cloud" if not self.is_local else "unverified"

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

    def build_prompt(self, metadata: dict[str, Any]) -> str:
        include_sensitive = self.endpoint_trust == "local" or bool(self.settings.get("include_sensitive_metadata", False))
        configured_fields = self.settings.get("metadata_fields")
        allowed_fields = set(configured_fields) if isinstance(configured_fields, list) else None
        return build_provider_prompt(metadata, include_sensitive=include_sensitive, allowed_fields=allowed_fields)


def _prompt_template() -> str:
    prompt_path = Path("prompts/image_classification.md")
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    packaged_prompt = files("photosage.resources").joinpath("image_classification.md")
    if packaged_prompt.is_file():
        return packaged_prompt.read_text(encoding="utf-8")
    return "Classify image content for a photo organization tool. Return JSON only."


def build_provider_prompt(
    metadata: dict[str, Any],
    include_sensitive: bool = False,
    allowed_fields: set[str] | None = None,
) -> str:
    """Build a provider prompt that asks only for factual classification JSON."""
    fields = allowed_fields or (set(metadata) if include_sensitive else SAFE_CLOUD_METADATA_FIELDS)
    safe_metadata = {
        key: value
        for key, value in metadata.items()
        if key in fields and key not in {"raw_metadata", "path", "absolute_path"} and value not in (None, "", [], {})
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
