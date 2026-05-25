from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from photosage.config import AppConfig
from photosage.providers.base import LOCAL_PROVIDERS
from photosage.providers.exceptions import ProviderError, ProviderUnavailableError
from photosage.providers.provider_factory import ProviderFactory
from photosage.providers.retry_handler import RetryConfig, run_with_retries

logger = logging.getLogger(__name__)


class ProviderManager:
    """Manage provider selection, fallback, retry, and local only policy."""

    def __init__(self, config: AppConfig, retry_config: RetryConfig | None = None) -> None:
        self.config = config
        self.retry_config = retry_config or RetryConfig(
            attempts=config.provider_retry_count,
            initial_delay_seconds=config.provider_retry_initial_delay,
        )

    def provider_order(self) -> list[str]:
        """Return provider order with the configured active provider first."""
        order = [self.config.vision_provider, *self.config.fallback_order]
        deduped: list[str] = []
        for provider in order:
            name = provider.lower().strip()
            if name and name not in deduped:
                deduped.append(name)

        if self.config.local_only:
            deduped = [name for name in deduped if name in LOCAL_PROVIDERS]
            if not deduped:
                deduped = ["ollama"]
        return deduped

    def analyze_image(self, image_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        """Analyze an image using provider fallback order."""
        errors: list[str] = []

        for provider_name in self.provider_order():
            try:
                provider = ProviderFactory.create(provider_name, self.config)
                logger.info("provider selected: %s local=%s", provider.provider_name, provider.is_local)
                started = time.perf_counter()
                response = run_with_retries(
                    lambda provider=provider: provider.analyze_image(image_path, metadata),
                    self.retry_config,
                )
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                logger.info("provider succeeded: %s elapsed_ms=%s", provider.provider_name, elapsed_ms)
                return response
            except ProviderError as error:
                logger.warning("provider failed: %s error=%s", provider_name, type(error).__name__)
                errors.append(f"{provider_name}: {type(error).__name__}")
                continue

        raise ProviderUnavailableError(f"No provider succeeded: {', '.join(errors)}")

