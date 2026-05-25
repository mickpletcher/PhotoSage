from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class AppConfig:
    vision_provider: str = "anthropic"
    metadata_threshold: int = 70
    dry_run_default: bool = True
    local_only: bool = False
    fallback_order: list[str] = field(default_factory=lambda: ["anthropic", "openai", "gemini", "ollama"])
    filename_format: str = "{date}_{location}_{subject}_{context}_{counter}"
    manifest_directory: Path = Path("manifests")
    log_file: Path = Path("logs/photosage.log")
    provider_settings: dict[str, dict[str, Any]] = field(default_factory=dict)
    provider_retry_count: int = 3
    provider_retry_initial_delay: float = 0.5
    recursive_scanning: bool = True
    thumbnail_size: int = 128
    log_level: str = "INFO"
    max_concurrent_ai_requests: int = 2


def load_config(config_path: Path = Path("config/settings.yaml")) -> AppConfig:
    """Load PhotoSage settings from YAML."""
    load_env_file(Path(".env"))
    if not config_path.exists():
        return AppConfig()

    with config_path.open("r", encoding="utf-8") as handle:
        data: dict[str, Any] = yaml.safe_load(handle) or {}

    return AppConfig(
        vision_provider=str(data.get("vision_provider", "anthropic")),
        metadata_threshold=int(data.get("metadata_threshold", 70)),
        dry_run_default=bool(data.get("dry_run_default", True)),
        local_only=bool(data.get("local_only", False)),
        fallback_order=list(data.get("fallback_order", ["anthropic", "openai", "gemini", "ollama"])),
        filename_format=str(data.get("filename_format", "{date}_{location}_{subject}_{context}_{counter}")),
        manifest_directory=Path(data.get("manifest_directory", "manifests")),
        log_file=Path(data.get("log_file", "logs/photosage.log")),
        provider_settings={
            "anthropic": dict(data.get("anthropic", {}) or {}),
            "openai": dict(data.get("openai", {}) or {}),
            "gemini": dict(data.get("gemini", {}) or {}),
            "ollama": dict(data.get("ollama", {}) or {}),
        },
        provider_retry_count=int(data.get("provider_retry_count", 3)),
        provider_retry_initial_delay=float(data.get("provider_retry_initial_delay", 0.5)),
        recursive_scanning=bool(data.get("recursive_scanning", True)),
        thumbnail_size=int(data.get("thumbnail_size", 128)),
        log_level=str(data.get("log_level", "INFO")),
        max_concurrent_ai_requests=int(data.get("max_concurrent_ai_requests", 2)),
    )


def config_to_dict(config: AppConfig) -> dict[str, Any]:
    """Convert app config to YAML serializable data."""
    data: dict[str, Any] = {
        "vision_provider": config.vision_provider,
        "metadata_threshold": config.metadata_threshold,
        "dry_run_default": config.dry_run_default,
        "local_only": config.local_only,
        "fallback_order": config.fallback_order,
        "filename_format": config.filename_format,
        "manifest_directory": str(config.manifest_directory),
        "log_file": str(config.log_file),
        "provider_retry_count": config.provider_retry_count,
        "provider_retry_initial_delay": config.provider_retry_initial_delay,
        "recursive_scanning": config.recursive_scanning,
        "thumbnail_size": config.thumbnail_size,
        "log_level": config.log_level,
        "max_concurrent_ai_requests": config.max_concurrent_ai_requests,
    }
    data.update(config.provider_settings)
    return data


def save_config(config: AppConfig, config_path: Path = Path("config/settings.yaml")) -> None:
    """Persist app config to YAML."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config_to_dict(config), handle, sort_keys=False)


def load_env_file(env_path: Path = Path(".env")) -> None:
    """Load simple KEY=VALUE pairs from a local env file without overriding the shell."""
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
