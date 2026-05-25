from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from photosage.providers.base import VisionProvider, build_provider_prompt
from photosage.providers.exceptions import ProviderUnavailableError


class OllamaProvider(VisionProvider):
    """Local Ollama multimodal provider."""

    provider_name = "ollama"
    default_model = "llava"
    is_local = True

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        super().__init__(settings=settings)
        self.endpoint = str(self.settings.get("endpoint") or "http://localhost:11434").rstrip("/")

    def analyze_image(self, image_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        """Analyze an image with a local Ollama multimodal model."""
        payload = {
            "model": self.model,
            "prompt": build_provider_prompt(metadata),
            "images": [self.image_as_base64(image_path)],
            "stream": False,
        }
        request = Request(
            f"{self.endpoint}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=float(self.settings.get("timeout", 60))) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, TimeoutError, json.JSONDecodeError) as error:
            raise ProviderUnavailableError(f"Ollama unavailable at {self.endpoint}") from error

        return self.normalize(body.get("response", ""))

