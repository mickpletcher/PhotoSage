from __future__ import annotations

import os
from dataclasses import dataclass
from importlib.util import find_spec
from typing import Any

import requests

from photosage.config import AppConfig
from photosage.providers.base import CLOUD_PROVIDERS
from photosage.providers.endpoint_policy import validate_local_endpoint
from photosage.providers.exceptions import ProviderError
from photosage.providers.ollama_provider import SUPPORTED_OLLAMA_MODELS


@dataclass(slots=True)
class ProviderHealth:
    """Provider health check result."""

    name: str
    status: str
    message: str
    endpoint: str = ""
    model: str = ""
    trust: str = "unknown"


def _module_available(name: str) -> bool:
    try:
        return find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def list_ollama_models(endpoint: str = "http://localhost:11434", timeout_seconds: float = 5) -> list[str]:
    """Return installed Ollama model names."""
    response = requests.get(f"{endpoint.rstrip('/')}/api/tags", timeout=timeout_seconds, allow_redirects=False)
    response.raise_for_status()
    payload = response.json()
    return sorted(model.get("name", "") for model in payload.get("models", []) if model.get("name"))


def get_ollama_version(endpoint: str = "http://localhost:11434", timeout_seconds: float = 5) -> str:
    """Return Ollama server version if available."""
    response = requests.get(f"{endpoint.rstrip('/')}/api/version", timeout=timeout_seconds, allow_redirects=False)
    response.raise_for_status()
    return str(response.json().get("version", "unknown"))


def list_lmstudio_models(endpoint: str = "http://localhost:1234/v1", timeout_seconds: float = 5) -> list[str]:
    """Return loaded or available LM Studio model ids from the OpenAI-compatible API."""
    response = requests.get(f"{endpoint.rstrip('/')}/models", timeout=timeout_seconds, allow_redirects=False)
    response.raise_for_status()
    payload = response.json()
    return sorted(model.get("id", "") for model in payload.get("data", []) if model.get("id"))


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

    try:
        trust = validate_local_endpoint(
            endpoint,
            settings.get("endpoint_allowlist"),
            bool(settings.get("allow_insecure_lan_endpoint", False)),
        )
    except ProviderError as error:
        return ProviderHealth("ollama", "ERROR", str(error), endpoint, model, "blocked")

    if model not in SUPPORTED_OLLAMA_MODELS:
        return ProviderHealth("ollama", "ERROR", f"Unsupported model '{model}'", endpoint, model, trust.classification)

    try:
        models = list_ollama_models(endpoint, timeout_seconds)
    except requests.RequestException:
        return ProviderHealth("ollama", "ERROR", f"Ollama server not reachable at {endpoint}", endpoint, model, trust.classification)

    if model not in models:
        return ProviderHealth(
            "ollama",
            "ERROR",
            f"Model '{model}' is not installed. Run: ollama pull {model}",
            endpoint,
            model,
            trust.classification,
        )
    return ProviderHealth("ollama", "OK", f"Ollama is available ({trust.classification})", endpoint, model, trust.classification)


def check_lmstudio(config: AppConfig) -> ProviderHealth:
    """Validate LM Studio endpoint and selected model."""
    settings = config.provider_settings.get("lmstudio", {})
    endpoint = str(settings.get("endpoint") or "http://localhost:1234/v1").rstrip("/")
    model = str(settings.get("model") or "local-vision-model")
    timeout_seconds = float(settings.get("healthcheck_timeout_seconds") or 5)

    try:
        trust = validate_local_endpoint(
            endpoint,
            settings.get("endpoint_allowlist"),
            bool(settings.get("allow_insecure_lan_endpoint", False)),
        )
    except ProviderError as error:
        return ProviderHealth("lmstudio", "ERROR", str(error), endpoint, model, "blocked")

    try:
        models = list_lmstudio_models(endpoint, timeout_seconds)
    except requests.RequestException:
        return ProviderHealth("lmstudio", "ERROR", f"LM Studio server not reachable at {endpoint}", endpoint, model, trust.classification)

    if model not in models:
        return ProviderHealth("lmstudio", "ERROR", f"Model '{model}' is not loaded in LM Studio", endpoint, model, trust.classification)
    return ProviderHealth("lmstudio", "OK", f"LM Studio is available ({trust.classification})", endpoint, model, trust.classification)


def check_openai_compatible(config: AppConfig) -> ProviderHealth:
    settings = config.provider_settings.get("openai_compatible_local", {})
    endpoint = str(settings.get("endpoint") or "http://localhost:8000/v1").rstrip("/")
    model = str(settings.get("model") or "local-vision-model")
    timeout_seconds = float(settings.get("healthcheck_timeout_seconds") or 5)
    try:
        trust = validate_local_endpoint(
            endpoint,
            settings.get("endpoint_allowlist"),
            bool(settings.get("allow_insecure_lan_endpoint", False)),
        )
        models = list_lmstudio_models(endpoint, timeout_seconds)
    except (ProviderError, requests.RequestException) as error:
        return ProviderHealth("openai_compatible_local", "ERROR", str(error), endpoint, model, "blocked")
    if model not in models:
        return ProviderHealth("openai_compatible_local", "ERROR", f"Model '{model}' is unavailable", endpoint, model, trust.classification)
    return ProviderHealth(
        "openai_compatible_local",
        "OK",
        f"OpenAI-compatible endpoint is available ({trust.classification})",
        endpoint,
        model,
        trust.classification,
    )


def check_providers(config: AppConfig) -> list[ProviderHealth]:
    """Return health status for all configured providers."""
    checks = [check_ollama(config), check_lmstudio(config), check_openai_compatible(config)]
    cloud_requirements = {
        "anthropic": ("ANTHROPIC_API_KEY", "anthropic"),
        "gemini": ("GOOGLE_API_KEY", "google.genai"),
        "kimi": ("MOONSHOT_API_KEY", "openai"),
        "openai": ("OPENAI_API_KEY", "openai"),
    }
    for provider in sorted(CLOUD_PROVIDERS):
        environment_name, module_name = cloud_requirements[provider]
        if config.local_only:
            status = "DISABLED"
            message = "Blocked by local_only mode"
        elif not os.getenv(environment_name):
            status = "ERROR"
            message = f"{environment_name} is not set"
        elif not _module_available(module_name):
            status = "ERROR"
            message = f"{module_name} SDK is not installed"
        else:
            status = "CONFIGURED"
            message = "Credentials and SDK found; no billable API request was made"
        model = str(config.provider_settings.get(provider, {}).get("model") or "")
        endpoint = "https://api.moonshot.ai/v1" if provider == "kimi" else ""
        checks.append(ProviderHealth(provider, status, message, endpoint=endpoint, model=model, trust="cloud"))
    return checks
