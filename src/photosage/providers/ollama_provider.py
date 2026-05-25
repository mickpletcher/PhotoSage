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
from photosage.providers.exceptions import InvalidResponseError, ProviderUnavailableError, UnsupportedModelError

logger = logging.getLogger(__name__)

SUPPORTED_OLLAMA_MODELS = {
    "llava",
    "llava:13b",
    "llava:34b",
    "bakllava",
    "minicpm-v",
    "qwen2.5vl",
    "moondream",
}


class OllamaProvider(VisionProvider):
    """Local Ollama multimodal provider."""

    provider_name = "ollama"
    default_model = "llava"
    is_local = True

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        super().__init__(settings=settings)
        self.endpoint = str(self.settings.get("endpoint") or "http://localhost:11434").rstrip("/")
        self.timeout_seconds = float(self.settings.get("timeout_seconds") or self.settings.get("timeout") or 180)
        self.temperature = float(self.settings.get("temperature", 0.1))
        self.max_dimension = int(self.settings.get("max_dimension", 1600))
        self.jpeg_quality = int(self.settings.get("jpeg_quality", 90))

    def analyze_image(self, image_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        """Analyze an image with a local Ollama multimodal model."""
        self.validate_supported_model()
        preprocessing_started = time.perf_counter()
        encoded_image = self.preprocess_image(image_path)
        preprocessing_ms = int((time.perf_counter() - preprocessing_started) * 1000)
        logger.info("ollama image preprocessing_ms=%s model=%s", preprocessing_ms, self.model)

        response_text = self._generate(encoded_image, metadata)
        try:
            return self.normalize(response_text)
        except InvalidResponseError:
            logger.warning("ollama malformed response; retrying once model=%s", self.model)
            response_text = self._generate(encoded_image, metadata, retry=True)
            return self.normalize(response_text)

    def validate_supported_model(self) -> None:
        """Validate that the selected model is supported by the integration."""
        if self.model not in SUPPORTED_OLLAMA_MODELS:
            raise UnsupportedModelError(
                f"Unsupported Ollama model '{self.model}'. Supported models: {', '.join(sorted(SUPPORTED_OLLAMA_MODELS))}"
            )

    def preprocess_image(self, image_path: Path) -> str:
        """Load, resize, convert, and base64 encode an image for Ollama."""
        try:
            with Image.open(image_path) as image:
                image = image.convert("RGB")
                image.thumbnail((self.max_dimension, self.max_dimension))
                buffer = BytesIO()
                image.save(buffer, format="JPEG", quality=self.jpeg_quality, optimize=True)
        except Exception as error:
            raise ProviderUnavailableError(f"Unable to preprocess image for Ollama: {image_path}") from error

        return base64.b64encode(buffer.getvalue()).decode("ascii")

    def _generate(self, encoded_image: str, metadata: dict[str, Any], retry: bool = False) -> str:
        payload = {
            "model": self.model,
            "prompt": build_provider_prompt(metadata),
            "images": [encoded_image],
            "stream": False,
            "options": {
                "temperature": self.temperature,
            },
        }

        started = time.perf_counter()
        try:
            response = requests.post(
                f"{self.endpoint}/api/generate",
                json=payload,
                timeout=self.timeout_seconds,
            )
        except requests.Timeout as error:
            raise ProviderUnavailableError(f"ERROR: Ollama request timed out at {self.endpoint}") from error
        except requests.RequestException as error:
            raise ProviderUnavailableError(f"ERROR: Ollama server not reachable at {self.endpoint}") from error

        response_ms = int((time.perf_counter() - started) * 1000)
        logger.info("ollama response_ms=%s model=%s retry=%s", response_ms, self.model, retry)

        if response.status_code == 404:
            raise ProviderUnavailableError(
                f"ERROR: Model '{self.model}' is not installed. Run: ollama pull {self.model}"
            )
        if response.status_code >= 400:
            raise ProviderUnavailableError(f"ERROR: Ollama request failed with HTTP {response.status_code}")

        try:
            body = response.json()
        except ValueError as error:
            raise InvalidResponseError("Ollama returned invalid JSON envelope") from error

        if "error" in body:
            message = str(body["error"])
            if "not found" in message.lower() or "pull" in message.lower():
                raise ProviderUnavailableError(f"ERROR: Model '{self.model}' is not installed. Run: ollama pull {self.model}")
            raise ProviderUnavailableError(f"ERROR: Ollama model failure: {message}")

        return str(body.get("response") or "")

