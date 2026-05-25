from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from photosage.config import AppConfig
from photosage.providers.base import CLOUD_PROVIDERS
from photosage.providers.ollama_provider import SUPPORTED_OLLAMA_MODELS


@dataclass(slots=True)
class ProviderHealth:
    """Provider health check result."""

    name: str
    status: str
    message: str
    endpoint: str = ""
    model: str = ""


def list_ollama_models(endpoint: str = "http://localhost:11434", timeout_seconds: float = 5) -> list[str]:
    """Return installed Ollama model names."""
    response = requests.get(f"{endpoint.rstrip('/')}/api/tags", timeout=timeout_seconds)
    response.raise_for_status()
    payload = response.json()
    return sorted(model.get("name", "") for model in payload.get("models", []) if model.get("name"))


def get_ollama_version(endpoint: str = "http://localhost:11434", timeout_seconds: float = 5) -> str:
    """Return Ollama server version if available."""
    response = requests.get(f"{endpoint.rstrip('/')}/api/version", timeout=timeout_seconds)
    response.raise_for_status()
    return str(response.json().get("version", "unknown"))


def ollama_info(endpoint: str = "http://localhost:11434", timeout_seconds: float = 5) -> dict[str, Any]:
    """Return best-effort Ollama diagnostics."""
    info: dict[str, Any] = {
        "endpoint": endpoint,
        "version": "unknown",
        "models": [],
        "gpu_usage": "unavailable",
        "vram_estimate": "unavailable",
        "inference_mode": "local",
    }
    try:
        info["version"] = get_ollama_version(endpoint, timeout_seconds)
    except requests.RequestException:
        pass
    try:
        info["models"] = list_ollama_models(endpoint, timeout_seconds)
    except requests.RequestException:
        pass
    return info


def check_ollama(config: AppConfig) -> ProviderHealth:
    """Validate Ollama endpoint and selected model."""
    settings = config.provider_settings.get("ollama", {})
    endpoint = str(settings.get("endpoint") or "http://localhost:11434").rstrip("/")
    model = str(settings.get("model") or "llava")
    timeout_seconds = float(settings.get("healthcheck_timeout_seconds") or 5)

    if model not in SUPPORTED_OLLAMA_MODELS:
        return ProviderHealth("ollama", "ERROR", f"Unsupported model '{model}'", endpoint, model)

    try:
        models = list_ollama_models(endpoint, timeout_seconds)
    except requests.RequestException:
        return ProviderHealth("ollama", "ERROR", f"Ollama server not reachable at {endpoint}", endpoint, model)

    if model not in models:
        return ProviderHealth("ollama", "ERROR", f"Model '{model}' is not installed. Run: ollama pull {model}", endpoint, model)
    return ProviderHealth("ollama", "OK", "Ollama is available", endpoint, model)


def check_providers(config: AppConfig) -> list[ProviderHealth]:
    """Return health status for all configured providers."""
    checks = [check_ollama(config)]
    for provider in sorted(CLOUD_PROVIDERS):
        status = "DISABLED" if config.local_only else "OK"
        message = "Blocked by local_only mode" if config.local_only else "Configured"
        model = str(config.provider_settings.get(provider, {}).get("model") or "")
        checks.append(ProviderHealth(provider, status, message, model=model))
    return checks
