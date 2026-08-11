from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from string import Formatter
from typing import Any

import yaml

PROVIDERS = {"anthropic", "openai", "gemini", "kimi", "ollama", "lmstudio", "openai_compatible_local"}
FOLDER_POLICIES = {"date-first", "location-first", "project-first", "custom"}
ASTRO_PROFILES = {"lunar", "solar", "planetary", "deep-sky"}
FILENAME_TOKENS = {
    "date",
    "location",
    "subject",
    "context",
    "counter",
    "app",
    "document_type",
    "media_type",
    "ocr_summary",
    "astro_profile",
    "astro_target",
    "telescope",
    "filter",
    "exposure",
    "capture_night",
    "session",
    "duration",
    "codec",
}
TOP_LEVEL_SETTINGS = {
    "vision_provider",
    "metadata_threshold",
    "dry_run_default",
    "local_only",
    "fallback_order",
    "filename_format",
    "manifest_directory",
    "log_file",
    "provider_retry_count",
    "provider_retry_initial_delay",
    "recursive_scanning",
    "thumbnail_size",
    "log_level",
    "max_concurrent_ai_requests",
    "watch_folders",
    "watch_stable_seconds",
    "duplicate_hash_distance",
    "detect_duplicates_during_rename",
    "geocode_cache_file",
    "geocode_cache_ttl_days",
    "folder_policy",
    "folder_keyword_map",
    "thumbnail_cache_directory",
    "profile_directory",
    "recent_manifest_file",
    "astro_profile",
    "astro_group_by_capture_night",
    "review_confidence_threshold",
    "require_manual_review_for_ai",
    "search_database",
    "embedding_backend",
    "embedding_model",
    *PROVIDERS,
}


class ConfigValidationError(ValueError):
    pass


def _boolean(data: dict[str, Any], key: str, default: bool) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ConfigValidationError(f"{key} must be true or false")
    return value


def _validate_filename_format(value: str) -> None:
    try:
        fields = {field for _, field, _, _ in Formatter().parse(value) if field}
    except ValueError as error:
        raise ConfigValidationError(f"filename_format is invalid: {error}") from error
    unknown = fields.difference(FILENAME_TOKENS)
    if unknown:
        raise ConfigValidationError(f"filename_format contains unsupported tokens: {sorted(unknown)}")
    if "counter" not in fields:
        raise ConfigValidationError("filename_format must include {counter} to prevent collisions")


def validate_config(config: AppConfig) -> AppConfig:
    if config.vision_provider not in PROVIDERS:
        raise ConfigValidationError(f"Unsupported vision_provider: {config.vision_provider}")
    unsupported_fallback = set(config.fallback_order).difference(PROVIDERS)
    if unsupported_fallback:
        raise ConfigValidationError(f"Unsupported fallback providers: {sorted(unsupported_fallback)}")
    if not 0 <= config.metadata_threshold <= 100:
        raise ConfigValidationError("metadata_threshold must be between 0 and 100")
    if config.provider_retry_count < 1:
        raise ConfigValidationError("provider_retry_count must be at least 1")
    if config.provider_retry_initial_delay < 0:
        raise ConfigValidationError("provider_retry_initial_delay cannot be negative")
    if config.max_concurrent_ai_requests < 1:
        raise ConfigValidationError("max_concurrent_ai_requests must be at least 1")
    if config.watch_stable_seconds < 0:
        raise ConfigValidationError("watch_stable_seconds cannot be negative")
    if not 0 <= config.duplicate_hash_distance <= 64:
        raise ConfigValidationError("duplicate_hash_distance must be between 0 and 64")
    if config.geocode_cache_ttl_days < 0:
        raise ConfigValidationError("geocode_cache_ttl_days cannot be negative")
    if config.thumbnail_size < 32 or config.thumbnail_size > 2048:
        raise ConfigValidationError("thumbnail_size must be between 32 and 2048")
    if config.log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ConfigValidationError(f"Unsupported log_level: {config.log_level}")
    if config.folder_policy not in FOLDER_POLICIES:
        raise ConfigValidationError(f"Unsupported folder_policy: {config.folder_policy}")
    if config.astro_profile not in ASTRO_PROFILES:
        raise ConfigValidationError(f"Unsupported astro_profile: {config.astro_profile}")
    if not 0 <= config.review_confidence_threshold <= 1:
        raise ConfigValidationError("review_confidence_threshold must be between 0 and 1")
    if config.embedding_backend not in {"hash", "ollama"}:
        raise ConfigValidationError("embedding_backend must be hash or ollama")
    kimi_settings = config.provider_settings.get("kimi", {})
    if kimi_settings.get("reasoning_effort", "low") not in {"low", "high", "max"}:
        raise ConfigValidationError("kimi.reasoning_effort must be low, high, or max")
    if kimi_settings.get("thinking", "enabled") not in {"enabled", "disabled"}:
        raise ConfigValidationError("kimi.thinking must be enabled or disabled")
    _validate_filename_format(config.filename_format)
    return config


@dataclass(slots=True)
class AppConfig:
    vision_provider: str = "ollama"
    metadata_threshold: int = 70
    dry_run_default: bool = True
    local_only: bool = True
    fallback_order: list[str] = field(default_factory=lambda: ["ollama", "lmstudio"])
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
    detect_duplicates_during_rename: bool = False
    geocode_cache_file: Path = Path(".photosage-cache/geocode_cache.json")
    geocode_cache_ttl_days: int = 365
    folder_policy: str = "date-first"
    folder_keyword_map: dict[str, str] = field(default_factory=dict)
    thumbnail_cache_directory: Path = Path(".photosage-cache/thumbnails")
    profile_directory: Path = Path(".photosage-cache/profiles")
    recent_manifest_file: Path = Path(".photosage-cache/recent_manifests.json")
    astro_profile: str = "deep-sky"
    astro_group_by_capture_night: bool = True
    review_confidence_threshold: float = 0.7
    require_manual_review_for_ai: bool = True
    search_database: Path = Path(".photosage-cache/search.sqlite3")
    embedding_backend: str = "hash"
    embedding_model: str = "nomic-embed-text"


def default_config_path() -> Path:
    repository_config = Path("config/settings.yaml")
    if repository_config.exists():
        return repository_config
    if os.name == "nt" and os.getenv("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "PhotoSage" / "settings.yaml"
    return Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "photosage" / "settings.yaml"


def load_config(config_path: Path | None = None) -> AppConfig:
    """Load PhotoSage settings from YAML."""
    config_path = config_path or default_config_path()
    load_env_file(config_path.parent / ".env")
    if config_path.parent != Path.cwd():
        load_env_file(Path(".env"))
    if not config_path.exists():
        return AppConfig()

    with config_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ConfigValidationError("Configuration must be a YAML mapping")
    data: dict[str, Any] = loaded
    unknown = set(data).difference(TOP_LEVEL_SETTINGS)
    if unknown:
        raise ConfigValidationError(f"Unknown configuration settings: {sorted(unknown)}")

    fallback_order = data.get("fallback_order", ["ollama", "lmstudio"])
    if not isinstance(fallback_order, list) or not all(isinstance(item, str) for item in fallback_order):
        raise ConfigValidationError("fallback_order must be a list of provider names")
    watch_folders = data.get("watch_folders", [])
    if not isinstance(watch_folders, list) or not all(isinstance(item, str) for item in watch_folders):
        raise ConfigValidationError("watch_folders must be a list of paths")
    for provider_name in PROVIDERS:
        settings = data.get(provider_name, {}) or {}
        if not isinstance(settings, dict):
            raise ConfigValidationError(f"{provider_name} settings must be a mapping")
        for boolean_key in ("include_sensitive_metadata", "allow_insecure_lan_endpoint", "allow_sensitive_embeddings"):
            if boolean_key in settings and not isinstance(settings[boolean_key], bool):
                raise ConfigValidationError(f"{provider_name}.{boolean_key} must be true or false")
        if "endpoint_allowlist" in settings and (
            not isinstance(settings["endpoint_allowlist"], list)
            or not all(isinstance(item, str) for item in settings["endpoint_allowlist"])
        ):
            raise ConfigValidationError(f"{provider_name}.endpoint_allowlist must be a list of hostnames")

    config = AppConfig(
        vision_provider=str(data.get("vision_provider", "ollama")),
        metadata_threshold=int(data.get("metadata_threshold", 70)),
        dry_run_default=_boolean(data, "dry_run_default", True),
        local_only=_boolean(data, "local_only", True),
        fallback_order=fallback_order,
        filename_format=str(data.get("filename_format", "{date}_{location}_{subject}_{context}_{counter}")),
        manifest_directory=Path(data.get("manifest_directory", "manifests")),
        log_file=Path(data.get("log_file", "logs/photosage.log")),
        provider_settings={
            "anthropic": dict(data.get("anthropic", {}) or {}),
            "openai": dict(data.get("openai", {}) or {}),
            "gemini": dict(data.get("gemini", {}) or {}),
            "kimi": dict(data.get("kimi", {}) or {}),
            "ollama": dict(data.get("ollama", {}) or {}),
            "lmstudio": dict(data.get("lmstudio", {}) or {}),
            "openai_compatible_local": dict(data.get("openai_compatible_local", {}) or {}),
        },
        provider_retry_count=int(data.get("provider_retry_count", 3)),
        provider_retry_initial_delay=float(data.get("provider_retry_initial_delay", 0.5)),
        recursive_scanning=_boolean(data, "recursive_scanning", True),
        thumbnail_size=int(data.get("thumbnail_size", 128)),
        log_level=str(data.get("log_level", "INFO")),
        max_concurrent_ai_requests=int(data.get("max_concurrent_ai_requests", 2)),
        watch_folders=[Path(path) for path in watch_folders],
        watch_stable_seconds=float(data.get("watch_stable_seconds", 5.0)),
        duplicate_hash_distance=int(data.get("duplicate_hash_distance", 5)),
        detect_duplicates_during_rename=_boolean(data, "detect_duplicates_during_rename", False),
        geocode_cache_file=Path(data.get("geocode_cache_file", ".photosage-cache/geocode_cache.json")),
        geocode_cache_ttl_days=int(data.get("geocode_cache_ttl_days", 365)),
        folder_policy=str(data.get("folder_policy", "date-first")),
        folder_keyword_map=dict(data.get("folder_keyword_map", {}) or {}),
        thumbnail_cache_directory=Path(data.get("thumbnail_cache_directory", ".photosage-cache/thumbnails")),
        profile_directory=Path(data.get("profile_directory", ".photosage-cache/profiles")),
        recent_manifest_file=Path(data.get("recent_manifest_file", ".photosage-cache/recent_manifests.json")),
        astro_profile=str(data.get("astro_profile", "deep-sky")),
        astro_group_by_capture_night=_boolean(data, "astro_group_by_capture_night", True),
        review_confidence_threshold=float(data.get("review_confidence_threshold", 0.7)),
        require_manual_review_for_ai=_boolean(data, "require_manual_review_for_ai", True),
        search_database=Path(data.get("search_database", ".photosage-cache/search.sqlite3")),
        embedding_backend=str(data.get("embedding_backend", "hash")),
        embedding_model=str(data.get("embedding_model", "nomic-embed-text")),
    )
    return validate_config(config)


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
        "detect_duplicates_during_rename": config.detect_duplicates_during_rename,
        "geocode_cache_file": str(config.geocode_cache_file),
        "geocode_cache_ttl_days": config.geocode_cache_ttl_days,
        "folder_policy": config.folder_policy,
        "folder_keyword_map": config.folder_keyword_map,
        "thumbnail_cache_directory": str(config.thumbnail_cache_directory),
        "profile_directory": str(config.profile_directory),
        "recent_manifest_file": str(config.recent_manifest_file),
        "astro_profile": config.astro_profile,
        "astro_group_by_capture_night": config.astro_group_by_capture_night,
        "review_confidence_threshold": config.review_confidence_threshold,
        "require_manual_review_for_ai": config.require_manual_review_for_ai,
        "search_database": str(config.search_database),
        "embedding_backend": config.embedding_backend,
        "embedding_model": config.embedding_model,
    }
    data.update(config.provider_settings)
    return data


def save_config(config: AppConfig, config_path: Path | None = None) -> None:
    """Persist app config to YAML."""
    validate_config(config)
    config_path = config_path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{config_path.name}.", suffix=".tmp", dir=config_path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            yaml.safe_dump(config_to_dict(config), handle, sort_keys=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, config_path)
    finally:
        temporary_path.unlink(missing_ok=True)


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
