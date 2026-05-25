from __future__ import annotations

from pathlib import Path
from typing import Any


APP_KEYWORDS = {
    "chrome": "chrome",
    "edge": "edge",
    "firefox": "firefox",
    "safari": "safari",
    "teams": "teams",
    "outlook": "outlook",
    "excel": "excel",
    "word": "word",
    "powerpoint": "powerpoint",
    "vscode": "vscode",
    "visual studio code": "vscode",
    "slack": "slack",
    "discord": "discord",
    "notion": "notion",
    "onenote": "onenote",
    "intune": "intune",
    "azure": "azure",
    "lightroom": "lightroom",
}

DOCUMENT_KEYWORDS = {
    "receipt": "receipt",
    "invoice": "invoice",
    "statement": "statement",
    "bill": "bill",
    "contract": "contract",
    "form": "form",
    "scan": "document",
    "scanned": "document",
    "document": "document",
    "note": "note",
    "email": "email",
    "spreadsheet": "spreadsheet",
    "presentation": "presentation",
}

SCREENSHOT_KEYWORDS = ("screenshot", "screen shot", "screen-capture", "screen_capture", "snip", "snipping")


def _metadata_text(metadata: dict[str, Any]) -> str:
    values: list[str] = []
    for key in ("original_filename", "title", "description", "camera_make", "camera_model", "lens_model"):
        value = metadata.get(key)
        if value:
            values.append(str(value))
    values.extend(str(value) for value in metadata.get("keywords") or [])
    values.extend(str(value) for value in metadata.get("tags") or [])
    raw_metadata = metadata.get("raw_metadata") or {}
    if isinstance(raw_metadata, dict):
        for key in ("Software", "Application", "CreatorTool", "ImageDescription", "XPTitle", "XPComment", "OCRText", "Text"):
            value = raw_metadata.get(key)
            if value:
                values.append(str(value))
    return " ".join(values).lower()


def detect_source_app(metadata: dict[str, Any]) -> str | None:
    """Return a source app label when metadata or filename strongly suggests one."""
    text = _metadata_text(metadata)
    for token, label in APP_KEYWORDS.items():
        if token in text:
            return label
    return None


def detect_document_type(metadata: dict[str, Any]) -> str | None:
    """Return a document type label when metadata or filename suggests one."""
    text = _metadata_text(metadata)
    for token, label in DOCUMENT_KEYWORDS.items():
        if token in text:
            return label
    return None


def is_screenshot(metadata: dict[str, Any]) -> bool:
    """Return true when a file appears to be a screenshot."""
    text = _metadata_text(metadata)
    if any(token in text for token in SCREENSHOT_KEYWORDS):
        return True
    original_filename = str(metadata.get("original_filename") or "")
    stem = Path(original_filename).stem.lower()
    return stem.startswith(("screenshot ", "screenshot-", "screenshot_", "screen shot "))


def ocr_summary_from_metadata(metadata: dict[str, Any], max_length: int = 80) -> str | None:
    """Return a short OCR summary from embedded metadata when available."""
    raw_metadata = metadata.get("raw_metadata") or {}
    candidates: list[Any] = []
    if isinstance(raw_metadata, dict):
        candidates.extend(raw_metadata.get(key) for key in ("OCRText", "Text", "ImageDescription", "XPComment"))
    candidates.extend(metadata.get(key) for key in ("description", "title"))
    for value in candidates:
        if not value:
            continue
        text = " ".join(str(value).split())
        if text:
            return text[:max_length].rstrip()
    return None


def classify_mixed_media(metadata: dict[str, Any]) -> dict[str, Any]:
    """Classify screenshots and document-like images from local metadata."""
    screenshot = is_screenshot(metadata)
    document_type = detect_document_type(metadata)
    source_app = detect_source_app(metadata)

    media_type = "photo"
    content_label = None
    if screenshot:
        media_type = "screenshot"
        content_label = "screenshot"
    elif document_type:
        media_type = "document"
        content_label = document_type

    if document_type == "receipt":
        media_type = "document"
        content_label = "receipt"

    tags = []
    if content_label:
        tags.append(content_label)
    if source_app:
        tags.append(source_app)
    if document_type and document_type not in tags:
        tags.append(document_type)

    return {
        "media_type": media_type,
        "content_label": content_label,
        "source_app": source_app,
        "document_type": document_type,
        "ocr_summary": ocr_summary_from_metadata(metadata) if media_type in {"document", "screenshot"} else None,
        "mixed_media_tags": tags,
    }
