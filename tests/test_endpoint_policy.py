import socket

import pytest

from photosage.providers.endpoint_policy import validate_local_endpoint
from photosage.providers.exceptions import ProviderUnavailableError


def _address(value):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (value, 0))]


def test_loopback_endpoint_is_local(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda host, port: _address("127.0.0.1"))
    assert validate_local_endpoint("http://localhost:11434").classification == "local"


def test_public_endpoint_is_blocked_even_when_allowlisted(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda host, port: _address("8.8.8.8"))
    with pytest.raises(ProviderUnavailableError, match="Public"):
        validate_local_endpoint("https://models.example.com", ["models.example.com"])


def test_lan_endpoint_requires_allowlist_and_https(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda host, port: _address("192.168.1.20"))
    with pytest.raises(ProviderUnavailableError, match="allowlisted"):
        validate_local_endpoint("https://ai.lan")
    assert validate_local_endpoint("https://ai.lan", ["ai.lan"]).classification == "lan"
    with pytest.raises(ProviderUnavailableError, match="HTTPS"):
        validate_local_endpoint("http://ai.lan", ["ai.lan"])
    assert validate_local_endpoint("http://ai.lan", ["ai.lan"], allow_insecure_lan=True).classification == "lan"
