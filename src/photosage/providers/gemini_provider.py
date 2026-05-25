from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from photosage.providers.base import VisionProvider, build_provider_prompt
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
            from google import genai
            from google.genai import types
        except ImportError as error:
            raise ProviderUnavailableError("google-genai SDK is not installed") from error

        client = genai.Client(api_key=api_key)
        image_bytes = image_path.read_bytes()
        media_type = "image/jpeg" if image_path.suffix.lower() in {".jpg", ".jpeg"} else f"image/{image_path.suffix.lower().lstrip('.')}"
        response = client.models.generate_content(
            model=self.model,
            contents=[
                build_provider_prompt(metadata),
                types.Part.from_bytes(data=image_bytes, mime_type=media_type),
            ],
        )
        return self.normalize(response.text or "")

