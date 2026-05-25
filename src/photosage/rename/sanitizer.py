from __future__ import annotations

import re
import unicodedata
from pathlib import Path

UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
NON_PORTABLE_CHARS = re.compile(r"[^a-z0-9._-]+")
SEPARATORS = re.compile(r"[-_]{2,}")
WINDOWS_RESERVED_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}


def _normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii")
    return text.strip().lower()


def sanitize_part(value: object, fallback: str = "unknown") -> str:
    """Sanitize one filename component for cross-platform use."""
    text = _normalize_text(value)
    text = UNSAFE_CHARS.sub(" ", text)
    text = re.sub(r"\s+", "-", text)
    text = NON_PORTABLE_CHARS.sub("-", text)
    text = SEPARATORS.sub("-", text)
    text = text.strip("-_.")

    if not text:
        text = fallback
    if text in WINDOWS_RESERVED_NAMES:
        text = f"{text}-file"
    return text


def sanitize_filename(filename: str, max_length: int = 180) -> str:
    """Sanitize and length limit a full filename while preserving extension."""
    path = Path(filename)
    extension = sanitize_part(path.suffix.lower().lstrip("."), "jpg")
    stem = sanitize_part(path.stem, "photo")
    available = max(1, max_length - len(extension) - 1)
    if len(stem) > available:
        stem = stem[:available].rstrip("-_.")
    if stem in WINDOWS_RESERVED_NAMES:
        stem = f"{stem}-file"
    return f"{stem}.{extension}"
