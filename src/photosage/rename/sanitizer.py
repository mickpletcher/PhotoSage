from __future__ import annotations

import re
from pathlib import Path

UNSAFE_CHARS = re.compile(r"[^a-z0-9._-]+")
SEPARATORS = re.compile(r"[-_]{2,}")


def sanitize_part(value: object, fallback: str = "unknown") -> str:
    """Sanitize one filename part."""
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", "-", text)
    text = UNSAFE_CHARS.sub("-", text)
    text = SEPARATORS.sub("-", text)
    text = text.strip("-_.")
    return text or fallback


def sanitize_filename(filename: str, max_length: int = 180) -> str:
    """Sanitize and length limit a full filename while preserving extension."""
    path = Path(filename)
    extension = sanitize_part(path.suffix.lower().lstrip("."), "jpg")
    stem = sanitize_part(path.stem, "photo")
    available = max_length - len(extension) - 1
    if len(stem) > available:
        stem = stem[:available].rstrip("-_.")
    return f"{stem}.{extension}"

