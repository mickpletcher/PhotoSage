from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from photosage.providers.base import VisionProvider, build_provider_prompt
from photosage.providers.exceptions import AuthenticationError, ProviderUnavailableError


class AnthropicProvider(VisionProvider):
    """Anthropic Claude multimodal vision provider."""

    provider_name = "anthropic"
    default_model = "claude-sonnet-4"

    def analyze_image(self, image_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        """Analyze an image with Anthropic Claude vision."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise AuthenticationError("ANTHROPIC_API_KEY is not set")

        try:
            import anthropic
        except ImportError as error:
            raise ProviderUnavailableError("anthropic SDK is not installed") from error

        media_type = "image/jpeg" if image_path.suffix.lower() in {".jpg", ".jpeg"} else f"image/{image_path.suffix.lower().lstrip('.')}"
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=int(self.settings.get("max_tokens", 800)),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": self.image_as_base64(image_path),
                            },
                        },
                        {"type": "text", "text": build_provider_prompt(metadata)},
                    ],
                }
            ],
        )
        text = "".join(getattr(block, "text", "") for block in response.content)
        return self.normalize(text)

