from __future__ import annotations

import json
import logging
import re
from typing import Any

from photosage.providers.exceptions import InvalidResponseError

logger = logging.getLogger(__name__)

RESPONSE_SCHEMA_KEYS = {
    "primary_subject",
    "secondary_subject",
    "activity",
    "environment",
    "location_guess",
    "confidence",
    "tags",
    "description",
    "provider",
    "model",
}

STRING_FIELDS = {
    "primary_subject",
    "secondary_subject",
    "activity",
    "environment",
    "location_guess",
    "description",
    "provider",
    "model",
}


def empty_response(provider: str = "", model: str = "") -> dict[str, Any]:
    """Return an empty normalized provider response."""
    return {
        "primary_subject": "",
        "secondary_subject": "",
        "activity": "",
        "environment": "",
        "location_guess": "",
        "confidence": 0.0,
        "tags": [],
        "description": "",
        "provider": provider,
        "model": model,
    }


def parse_json_payload(payload: str | dict[str, Any]) -> dict[str, Any]:
    """Parse provider JSON and repair minor formatting issues."""
    if isinstance(payload, dict):
        return payload

    text = payload.strip()
    text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()

    if "{" in text and "}" in text:
        text = text[text.find("{") : text.rfind("}") + 1]

    text = re.sub(r",\s*([}\]])", r"\1", text)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as error:
        raise InvalidResponseError(f"Provider returned invalid JSON: {error}") from error

    if not isinstance(parsed, dict):
        raise InvalidResponseError("Provider response JSON must be an object")
    return parsed


def normalize_response(payload: str | dict[str, Any], provider: str, model: str) -> dict[str, Any]:
    """Normalize provider output into the PhotoSage response contract."""
    parsed = parse_json_payload(payload)
    normalized = empty_response(provider=provider, model=model)
    normalized.update({key: parsed.get(key, normalized[key]) for key in RESPONSE_SCHEMA_KEYS})

    for key in STRING_FIELDS:
        normalized[key] = "" if normalized[key] is None else str(normalized[key]).strip()

    try:
        confidence = float(normalized["confidence"])
    except (TypeError, ValueError):
        confidence = 0.0
    normalized["confidence"] = max(0.0, min(1.0, confidence))

    tags = normalized.get("tags")
    if tags is None:
        tags = []
    elif isinstance(tags, str):
        tags = [tag.strip() for tag in re.split(r"[,;]", tags) if tag.strip()]
    elif not isinstance(tags, list):
        tags = [str(tags)]

    normalized["tags"] = sorted({str(tag).strip().lower() for tag in tags if str(tag).strip()})
    normalized["provider"] = provider
    normalized["model"] = model
    logger.info("normalized response from provider=%s model=%s", provider, model)
    return normalized

