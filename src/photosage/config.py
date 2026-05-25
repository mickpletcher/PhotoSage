from __future__ import annotations

from dataclasses import dataclass, field
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


def load_config(config_path: Path = Path("config/settings.yaml")) -> AppConfig:
    """Load PhotoSage settings from YAML."""
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
    )
