from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from photosage.providers.base import VisionProvider, build_provider_prompt
from photosage.providers.exceptions import AuthenticationError, ProviderUnavailableError


class OpenAIProvider(VisionProvider):
    """OpenAI vision capable model provider."""

    provider_name = "openai"
    default_model = "gpt-4.1-mini"

    def analyze_image(self, image_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        """Analyze an image with an OpenAI vision model."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise AuthenticationError("OPENAI_API_KEY is not set")

        try:
            from openai import OpenAI
        except ImportError as error:
            raise ProviderUnavailableError("openai SDK is not installed") from error

        media_type = "image/jpeg" if image_path.suffix.lower() in {".jpg", ".jpeg"} else f"image/{image_path.suffix.lower().lstrip('.')}"
        image_url = f"data:{media_type};base64,{self.image_as_base64(image_path)}"
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": build_provider_prompt(metadata)},
                        {"type": "input_image", "image_url": image_url},
                    ],
                }
            ],
        )
        return self.normalize(response.output_text)

