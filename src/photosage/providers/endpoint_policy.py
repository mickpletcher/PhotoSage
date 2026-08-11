from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

from photosage.providers.exceptions import ProviderUnavailableError


@dataclass(frozen=True, slots=True)
class EndpointTrust:
    endpoint: str
    host: str
    classification: str


def _resolved_addresses(host: str) -> set[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        return {ipaddress.ip_address(str(item[4][0]).split("%", 1)[0]) for item in socket.getaddrinfo(host, None)}
    except (OSError, ValueError) as error:
        raise ProviderUnavailableError(f"Unable to resolve provider endpoint host: {host}") from error


def validate_local_endpoint(
    endpoint: str,
    allowlist: list[str] | tuple[str, ...] | set[str] | None = None,
    allow_insecure_lan: bool = False,
) -> EndpointTrust:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ProviderUnavailableError("Local provider endpoint must use http or https and include a hostname")
    if parsed.username or parsed.password:
        raise ProviderUnavailableError("Provider endpoint credentials are not allowed in URLs")

    host = parsed.hostname.lower().rstrip(".")
    addresses = _resolved_addresses(host)
    if not addresses:
        raise ProviderUnavailableError(f"Provider endpoint did not resolve: {host}")
    if all(address.is_loopback for address in addresses):
        return EndpointTrust(endpoint, host, "local")

    trusted_hosts = {str(value).lower().rstrip(".") for value in allowlist or []}
    if host not in trusted_hosts:
        raise ProviderUnavailableError(f"LAN provider endpoint is not allowlisted: {host}")
    if any(not (address.is_private or address.is_link_local) for address in addresses):
        raise ProviderUnavailableError(f"Public provider endpoint is blocked for a local provider: {host}")
    if parsed.scheme != "https" and not allow_insecure_lan:
        raise ProviderUnavailableError("LAN provider endpoints require HTTPS unless allow_insecure_lan_endpoint is enabled")
    return EndpointTrust(endpoint, host, "lan")
