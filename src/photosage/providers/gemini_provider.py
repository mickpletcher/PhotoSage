from __future__ import annotations

import os
from importlib import import_module
from pathlib import Path
from typing import Any

from photosage.providers.base import VisionProvider
from photosage.providers.exceptions import AuthenticationError, ProviderUnavailableError


class GeminiProvider(VisionProvider):
    """Google Gemini multimodal provider."""

    provider_name = "gemini"
    default_model = "gemini-2.5-pro"

    def analyze_image(self, image_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        """Analyze an image with Gemini multimodal APIs."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise AuthenticationError("GOOGLE_API_KEY is not set")

        try:
            genai: Any = import_module("google.genai")
            types: Any = import_module("google.genai.types")
        except ImportError as error:
            raise ProviderUnavailableError("google-genai SDK is not installed") from error

        client: Any = genai.Client(api_key=api_key)
        image_bytes = image_path.read_bytes()
        media_type = "image/jpeg" if image_path.suffix.lower() in {".jpg", ".jpeg"} else f"image/{image_path.suffix.lower().lstrip('.')}"
        try:
            response = client.models.generate_content(
                model=self.model,
                contents=[
                    self.build_prompt(metadata),
                    types.Part.from_bytes(data=image_bytes, mime_type=media_type),
                ],
            )
        except Exception as error:
            raise ProviderUnavailableError(f"Gemini request failed: {type(error).__name__}") from error
        return self.normalize(response.text or "")
