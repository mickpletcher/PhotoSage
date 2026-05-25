import pytest

from photosage.providers.exceptions import AuthenticationError, InvalidResponseError, RetryLimitExceededError
from photosage.providers.retry_handler import RetryConfig, run_with_retries


def test_retry_handler_retries_invalid_response_then_succeeds():
    calls = {"count": 0}

    def operation():
        calls["count"] += 1
        if calls["count"] < 2:
            raise InvalidResponseError("bad json")
        return "ok"

    result = run_with_retries(operation, RetryConfig(attempts=3, initial_delay_seconds=0))

    assert result == "ok"
    assert calls["count"] == 2


def test_retry_handler_stops_after_limit():
    with pytest.raises(RetryLimitExceededError):
        run_with_retries(
            lambda: (_ for _ in ()).throw(InvalidResponseError("bad json")),
            RetryConfig(attempts=2, initial_delay_seconds=0),
        )


def test_retry_handler_does_not_retry_authentication_errors():
    calls = {"count": 0}

    def operation():
        calls["count"] += 1
        raise AuthenticationError("missing key")

    with pytest.raises(AuthenticationError):
        run_with_retries(operation, RetryConfig(attempts=3, initial_delay_seconds=0))

    assert calls["count"] == 1

