from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from dateutil import parser


ASTRO_PROFILES = {"lunar", "solar", "planetary", "deep-sky"}
FITS_EXTENSIONS = {".fit", ".fits"}
FITS_SIDECAREXTENSIONS = [".fits", ".fit"]


def read_fits_header(path: Path) -> dict[str, str]:
    if not path.exists() or path.suffix.lower() not in FITS_EXTENSIONS:
        return {}

    header: dict[str, str] = {}
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(2880), b""):
                text = block.decode("ascii", errors="ignore")
                for index in range(0, len(text), 80):
                    card = text[index : index + 80]
                    keyword = card[:8].strip()
                    if keyword == "END":
                        return header
                    if not keyword or "=" not in card[:10]:
                        continue
                    value = card[10:80].split("/", 1)[0].strip().strip("'").strip()
                    header[keyword] = value
    except OSError:
        return {}
    return header


def sidecar_fits_path(image_path: Path) -> Path | None:
    for extension in FITS_SIDECAREXTENSIONS:
        candidate = image_path.with_suffix(extension)
        if candidate.exists():
            return candidate
    return None


def fits_header_for_image(image_path: Path) -> dict[str, str]:
    if image_path.suffix.lower() in FITS_EXTENSIONS:
        return read_fits_header(image_path)
    sidecar = sidecar_fits_path(image_path)
    return read_fits_header(sidecar) if sidecar else {}


def enrich_astro_metadata(metadata: dict[str, Any], image_path: Path) -> dict[str, Any]:
    header = fits_header_for_image(image_path)
    filename_text = image_path.stem.lower().replace("_", " ").replace("-", " ")
    keywords = [str(value).lower() for value in metadata.get("keywords", []) + metadata.get("tags", [])]
    combined = " ".join([filename_text, *keywords, str(metadata.get("description") or ""), str(metadata.get("title") or "")]).lower()

    target = _first(header, "OBJECT", "OBJCTRA") or _target_from_text(combined)
    profile = _profile_from_text(combined, target)
    telescope = _first(header, "TELESCOP", "INSTRUME") or _telescope_from_text(combined)
    filter_name = _first(header, "FILTER", "FILTERID") or _filter_from_text(combined)
    exposure = _first(header, "EXPTIME", "EXPOSURE")
    capture_date = _parse_date(_first(header, "DATE-OBS", "DATE")) or metadata.get("date_taken") or metadata.get("modified_date")

    is_astro = bool(header or target or telescope or filter_name or profile)
    if not is_astro:
        return metadata

    enriched = dict(metadata)
    enriched["astro_mode"] = True
    enriched["astro_profile"] = profile or "deep-sky"
    enriched["astro_target"] = target or "sky"
    enriched["astro_telescope"] = telescope or ""
    enriched["astro_filter"] = filter_name or ""
    enriched["astro_exposure"] = str(exposure or "")
    enriched["astro_capture_night"] = capture_night(capture_date)
    enriched["astro_session_id"] = session_id(enriched["astro_capture_night"], enriched["astro_target"], enriched["astro_profile"])
    enriched["fits_detected"] = bool(header)
    enriched["fits_metadata"] = header
    enriched["content_label"] = enriched.get("content_label") or enriched["astro_profile"]
    tags = set(enriched.get("tags") or [])
    tags.update({"astrophotography", enriched["astro_profile"]})
    if enriched["astro_target"]:
        tags.add(str(enriched["astro_target"]))
    enriched["tags"] = sorted(tags)
    return enriched


def capture_night(value: Any) -> str:
    parsed = _parse_date(value)
    if parsed is None:
        return "unknown-night"
    if parsed.hour < 12:
        parsed = parsed - timedelta(days=1)
    return parsed.date().isoformat()


def session_id(capture_night_value: str, target: str, profile: str) -> str:
    parts = [capture_night_value, _token(target or "sky"), _token(profile or "astro")]
    return "_".join(part for part in parts if part)


def group_by_capture_night(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        metadata = item.get("metadata") or item
        key = metadata.get("astro_capture_night") or "unknown-night"
        groups.setdefault(str(key), []).append(item)
    return groups


def _first(values: dict[str, str], *keys: str) -> str | None:
    for key in keys:
        value = values.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def _parse_date(value: Any) -> datetime | None:
    if not value:
        return None
    if hasattr(value, "date"):
        return value
    try:
        return parser.parse(str(value).replace("T", " "))
    except (TypeError, ValueError, OverflowError):
        return None


def _target_from_text(text: str) -> str | None:
    known = {
        "orion nebula": "orion-nebula",
        "m42": "orion-nebula",
        "andromeda": "andromeda-galaxy",
        "m31": "andromeda-galaxy",
        "pleiades": "pleiades",
        "m45": "pleiades",
        "moon": "moon",
        "lunar": "moon",
        "sun": "sun",
        "solar": "sun",
        "jupiter": "jupiter",
        "saturn": "saturn",
        "mars": "mars",
    }
    for needle, target in known.items():
        if needle in text:
            return target
    return None


def _profile_from_text(text: str, target: str | None) -> str | None:
    if any(word in text for word in ["solar", "h-alpha", "halpha"]) or target == "sun":
        return "solar"
    if any(word in text for word in ["moon", "lunar"]) or target == "moon":
        return "lunar"
    if any(word in text for word in ["jupiter", "saturn", "mars", "planetary"]):
        return "planetary"
    if any(word in text for word in ["nebula", "galaxy", "cluster", "deep sky", "deepsky", "m42", "m31", "m45"]):
        return "deep-sky"
    return None


def _telescope_from_text(text: str) -> str | None:
    known = ["seestar-s50", "seestar", "evscope", "redcat", "c8", "c11", "askar", "siril"]
    for value in known:
        if value in text:
            return "seestar-s50" if value == "seestar" else value
    return None


def _filter_from_text(text: str) -> str | None:
    filters = {
        "h-alpha": "h-alpha",
        "halpha": "h-alpha",
        "ha": "h-alpha",
        "oiii": "oiii",
        "sii": "sii",
        "l-pro": "l-pro",
        "uv-ir": "uv-ir-cut",
    }
    for needle, value in filters.items():
        if needle in text:
            return value
    return None


def _token(value: str) -> str:
    return str(value).strip().lower().replace(" ", "-").replace("_", "-")
