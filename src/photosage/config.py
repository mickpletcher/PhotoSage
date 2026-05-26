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
    fallback_order: list[str] = field(default_factory=lambda: ["anthropic", "openai", "gemini", "ollama", "lmstudio"])
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
    watch_folders: list[Path] = field(default_factory=list)
    watch_stable_seconds: float = 5.0
    duplicate_hash_distance: int = 5
    geocode_cache_file: Path = Path(".photosage-cache/geocode_cache.json")
    geocode_cache_ttl_days: int = 365
    folder_policy: str = "date-first"
    folder_keyword_map: dict[str, str] = field(default_factory=dict)
    thumbnail_cache_directory: Path = Path(".photosage-cache/thumbnails")
    profile_directory: Path = Path(".photosage-cache/profiles")
    recent_manifest_file: Path = Path(".photosage-cache/recent_manifests.json")
    astro_profile: str = "deep-sky"
    astro_group_by_capture_night: bool = True


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
        fallback_order=list(data.get("fallback_order", ["anthropic", "openai", "gemini", "ollama", "lmstudio"])),
        filename_format=str(data.get("filename_format", "{date}_{location}_{subject}_{context}_{counter}")),
        manifest_directory=Path(data.get("manifest_directory", "manifests")),
        log_file=Path(data.get("log_file", "logs/photosage.log")),
        provider_settings={
            "anthropic": dict(data.get("anthropic", {}) or {}),
            "openai": dict(data.get("openai", {}) or {}),
            "gemini": dict(data.get("gemini", {}) or {}),
            "ollama": dict(data.get("ollama", {}) or {}),
            "lmstudio": dict(data.get("lmstudio", {}) or {}),
        },
        provider_retry_count=int(data.get("provider_retry_count", 3)),
        provider_retry_initial_delay=float(data.get("provider_retry_initial_delay", 0.5)),
        recursive_scanning=bool(data.get("recursive_scanning", True)),
        thumbnail_size=int(data.get("thumbnail_size", 128)),
        log_level=str(data.get("log_level", "INFO")),
        max_concurrent_ai_requests=int(data.get("max_concurrent_ai_requests", 2)),
        watch_folders=[Path(path) for path in data.get("watch_folders", [])],
        watch_stable_seconds=float(data.get("watch_stable_seconds", 5.0)),
        duplicate_hash_distance=int(data.get("duplicate_hash_distance", 5)),
        geocode_cache_file=Path(data.get("geocode_cache_file", ".photosage-cache/geocode_cache.json")),
        geocode_cache_ttl_days=int(data.get("geocode_cache_ttl_days", 365)),
        folder_policy=str(data.get("folder_policy", "date-first")),
        folder_keyword_map=dict(data.get("folder_keyword_map", {}) or {}),
        thumbnail_cache_directory=Path(data.get("thumbnail_cache_directory", ".photosage-cache/thumbnails")),
        profile_directory=Path(data.get("profile_directory", ".photosage-cache/profiles")),
        recent_manifest_file=Path(data.get("recent_manifest_file", ".photosage-cache/recent_manifests.json")),
        astro_profile=str(data.get("astro_profile", "deep-sky")),
        astro_group_by_capture_night=bool(data.get("astro_group_by_capture_night", True)),
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
        "watch_folders": [str(path) for path in config.watch_folders],
        "watch_stable_seconds": config.watch_stable_seconds,
        "duplicate_hash_distance": config.duplicate_hash_distance,
        "geocode_cache_file": str(config.geocode_cache_file),
        "geocode_cache_ttl_days": config.geocode_cache_ttl_days,
        "folder_policy": config.folder_policy,
        "folder_keyword_map": config.folder_keyword_map,
        "thumbnail_cache_directory": str(config.thumbnail_cache_directory),
        "profile_directory": str(config.profile_directory),
        "recent_manifest_file": str(config.recent_manifest_file),
        "astro_profile": config.astro_profile,
        "astro_group_by_capture_night": config.astro_group_by_capture_night,
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
