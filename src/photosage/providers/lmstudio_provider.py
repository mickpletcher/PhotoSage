from __future__ import annotations

import base64
import logging
import time
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
from PIL import Image

from photosage.providers.base import VisionProvider, build_provider_prompt
from photosage.providers.exceptions import InvalidResponseError, ProviderUnavailableError

logger = logging.getLogger(__name__)


class LMStudioProvider(VisionProvider):
    provider_name = "lmstudio"
    default_model = "local-vision-model"
    is_local = True

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        super().__init__(settings=settings)
        self.endpoint = str(self.settings.get("endpoint") or "http://localhost:1234/v1").rstrip("/")
        self.timeout_seconds = float(self.settings.get("timeout_seconds") or self.settings.get("timeout") or 180)
        self.temperature = float(self.settings.get("temperature", 0.1))
        self.max_dimension = int(self.settings.get("max_dimension", 1600))
        self.jpeg_quality = int(self.settings.get("jpeg_quality", 90))

    def analyze_image(self, image_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter()
        encoded_image = self.preprocess_image(image_path)
        preprocessing_ms = int((time.perf_counter() - started) * 1000)
        logger.info("lmstudio image preprocessing_ms=%s model=%s", preprocessing_ms, self.model)

        response_text = self._chat_completion(encoded_image, metadata)
        try:
            return self.normalize(response_text)
        except InvalidResponseError:
            logger.warning("lmstudio malformed response; retrying once model=%s", self.model)
            response_text = self._chat_completion(encoded_image, metadata, retry=True)
            return self.normalize(response_text)

    def preprocess_image(self, image_path: Path) -> str:
        try:
            with Image.open(image_path) as image:
                image = image.convert("RGB")
                image.thumbnail((self.max_dimension, self.max_dimension))
                buffer = BytesIO()
                image.save(buffer, format="JPEG", quality=self.jpeg_quality, optimize=True)
        except Exception as error:
            raise ProviderUnavailableError(f"Unable to preprocess image for LM Studio: {image_path}") from error
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"

    def _chat_completion(self, encoded_image: str, metadata: dict[str, Any], retry: bool = False) -> str:
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": build_provider_prompt(metadata)},
                        {"type": "image_url", "image_url": {"url": encoded_image}},
                    ],
                }
            ],
        }
        started = time.perf_counter()
        try:
            response = requests.post(f"{self.endpoint}/chat/completions", json=payload, timeout=self.timeout_seconds)
        except requests.Timeout as error:
            raise ProviderUnavailableError(f"ERROR: LM Studio request timed out at {self.endpoint}") from error
        except requests.RequestException as error:
            raise ProviderUnavailableError(f"ERROR: LM Studio server not reachable at {self.endpoint}") from error

        response_ms = int((time.perf_counter() - started) * 1000)
        logger.info("lmstudio response_ms=%s model=%s retry=%s", response_ms, self.model, retry)

        if response.status_code == 404:
            raise ProviderUnavailableError(f"ERROR: LM Studio model or endpoint is unavailable at {self.endpoint}")
        if response.status_code >= 400:
            raise ProviderUnavailableError(f"ERROR: LM Studio request failed with HTTP {response.status_code}")

        try:
            body = response.json()
        except ValueError as error:
            raise InvalidResponseError("LM Studio returned invalid JSON envelope") from error

        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise InvalidResponseError("LM Studio returned an invalid chat completion envelope") from error

        if isinstance(content, list):
            return "\n".join(str(part.get("text") or "") for part in content if isinstance(part, dict))
        return str(content or "")
