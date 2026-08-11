from __future__ import annotations

from typing import Any

from photosage.providers.lmstudio_provider import LMStudioProvider


class OpenAICompatibleLocalProvider(LMStudioProvider):
    provider_name = "openai_compatible_local"
    default_model = "local-vision-model"

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        merged = {"endpoint": "http://localhost:8000/v1", **(settings or {})}
        super().__init__(merged)
