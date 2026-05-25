from __future__ import annotations


class ProviderError(Exception):
    """Base provider exception."""


class AuthenticationError(ProviderError):
    """Provider credentials are missing or invalid."""


class InvalidResponseError(ProviderError):
    """Provider returned invalid or unusable structured output."""


class ProviderUnavailableError(ProviderError):
    """Provider SDK, endpoint, or model is unavailable."""


class RetryLimitExceededError(ProviderError):
    """Retry attempts were exhausted."""


class UnsupportedProviderError(ProviderError):
    """Requested provider is not supported."""

