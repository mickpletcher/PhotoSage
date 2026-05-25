from __future__ import annotations

from pathlib import Path


class CatalogSafetyError(RuntimeError):
    """Lightroom catalog safety check failed."""


def detect_lightroom_catalog_risk(path: Path) -> list[str]:
    """Return warnings for probable Lightroom catalog locations."""
    warnings: list[str] = []
    resolved = path.resolve(strict=False)
    parts = {part.lower() for part in resolved.parts}
    if any(part.endswith(".lrdata") for part in parts):
        warnings.append("Path is inside a Lightroom .lrdata support folder.")
    if list(resolved.glob("*.lrcat")):
        warnings.append("Directory contains a Lightroom .lrcat catalog file.")
    if list(resolved.rglob("*.lrcat")):
        warnings.append("Directory tree contains a Lightroom .lrcat catalog file.")
    if "lightroom catalog previews.lrdata" in parts:
        warnings.append("Path appears to be a Lightroom previews folder.")
    return sorted(set(warnings))


def validate_lightroom_export_directory(path: Path, force_catalog_modify: bool = False) -> list[str]:
    """Block probable catalog modifications unless explicitly forced."""
    warnings = detect_lightroom_catalog_risk(path)
    if warnings and not force_catalog_modify:
        raise CatalogSafetyError("Unsafe Lightroom catalog location blocked: " + " ".join(warnings))
    return warnings

