from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Any

from photosage.providers.base import VisionProvider
from photosage.providers.exceptions import AuthenticationError, InvalidResponseError, ProviderUnavailableError

KIMI_BASE_URL = "https://api.moonshot.ai/v1"


class KimiProvider(VisionProvider):
    """Moonshot AI Kimi multimodal provider."""

    provider_name = "kimi"
    default_model = "kimi-k3"

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        super().__init__(settings)
        self.base_url = str(self.settings.get("base_url") or KIMI_BASE_URL).rstrip("/")
        if self.base_url != KIMI_BASE_URL:
            raise ProviderUnavailableError(f"Kimi base_url must be {KIMI_BASE_URL}")

    def analyze_image(self, image_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        api_key = os.getenv("MOONSHOT_API_KEY")
        if not api_key:
            raise AuthenticationError("MOONSHOT_API_KEY is not set")

        try:
            from openai import OpenAI
        except ImportError as error:
            raise ProviderUnavailableError("openai SDK is not installed") from error

        media_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
        image_url = f"data:{media_type};base64,{self.image_as_base64(image_path)}"
        client: Any = OpenAI(
            api_key=api_key,
            base_url=self.base_url,
            timeout=float(self.settings.get("timeout_seconds", 180)),
        )
        request: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": self.build_prompt(metadata)},
                    ],
                }
            ],
            "response_format": {"type": "json_object"},
        }
        if self.model == "kimi-k3":
            request["reasoning_effort"] = str(self.settings.get("reasoning_effort") or "low")
            request["max_completion_tokens"] = int(self.settings.get("max_completion_tokens", 1200))
        else:
            request["max_tokens"] = int(self.settings.get("max_tokens", 1200))
            if self.model in {"kimi-k2.5", "kimi-k2.6"} and self.settings.get("thinking"):
                request["thinking"] = {"type": str(self.settings["thinking"])}

        try:
            response = client.chat.completions.create(**request)
        except Exception as error:
            if getattr(error, "status_code", None) in {401, 403}:
                raise AuthenticationError("Kimi API credentials were rejected") from error
            raise ProviderUnavailableError(f"Kimi request failed: {type(error).__name__}") from error

        if not response.choices:
            raise InvalidResponseError("Kimi returned no completion choices")
        choice = response.choices[0]
        if getattr(choice, "finish_reason", None) == "length":
            raise InvalidResponseError("Kimi response was truncated; increase the configured token limit")
        content = getattr(choice.message, "content", None)
        if not isinstance(content, str) or not content.strip():
            raise InvalidResponseError("Kimi returned an empty response")
        return self.normalize(content)
