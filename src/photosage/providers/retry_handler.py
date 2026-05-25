from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from photosage.providers.exceptions import (
    AuthenticationError,
    InvalidResponseError,
    ProviderUnavailableError,
    RetryLimitExceededError,
    UnsupportedProviderError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(slots=True)
class RetryConfig:
    """Retry settings for provider calls."""

    attempts: int = 3
    initial_delay_seconds: float = 0.5
    backoff_factor: float = 2.0


NON_RETRYABLE = (AuthenticationError, UnsupportedProviderError)
RETRYABLE = (InvalidResponseError, ProviderUnavailableError, TimeoutError, ConnectionError)


def run_with_retries(operation: Callable[[], T], config: RetryConfig | None = None) -> T:
    """Run an operation with exponential backoff for retryable failures."""
    retry_config = config or RetryConfig()
    delay = retry_config.initial_delay_seconds
    last_error: Exception | None = None

    for attempt in range(1, retry_config.attempts + 1):
        try:
            return operation()
        except NON_RETRYABLE:
            raise
        except RETRYABLE as error:
            last_error = error
            logger.warning("provider retry %s/%s after %s", attempt, retry_config.attempts, type(error).__name__)
            if attempt >= retry_config.attempts:
                break
            time.sleep(delay)
            delay *= retry_config.backoff_factor

    raise RetryLimitExceededError(f"Retry limit exceeded: {last_error}") from last_error

