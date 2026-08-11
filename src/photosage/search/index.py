from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from photosage.config import AppConfig
from photosage.metadata.exif_reader import extract_metadata
from photosage.providers.endpoint_policy import validate_local_endpoint
from photosage.scanner import scan_images

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _text(path: Path, metadata: dict[str, Any]) -> str:
    values: list[str] = [path.stem]
    for key in ("title", "description", "content_label", "document_type", "source_app", "camera_model", "location"):
        if metadata.get(key):
            values.append(str(metadata[key]))
    for key in ("keywords", "tags", "mixed_media_tags"):
        values.extend(str(value) for value in metadata.get(key) or [])
    return " ".join(values)


def hash_embedding(text: str, dimensions: int = 256) -> list[float]:
    vector = [0.0] * dimensions
    for token in TOKEN_PATTERN.findall(text.lower()):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        number = int.from_bytes(digest, "big")
        vector[number % dimensions] += 1.0 if number & 1 else -1.0
    magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / magnitude for value in vector]


def ollama_embedding(text: str, config: AppConfig) -> list[float]:
    settings = config.provider_settings.get("ollama", {})
    endpoint = str(settings.get("endpoint") or "http://localhost:11434").rstrip("/")
    trust = validate_local_endpoint(
        endpoint,
        settings.get("endpoint_allowlist"),
        bool(settings.get("allow_insecure_lan_endpoint", False)),
    )
    if trust.classification != "local" and not bool(settings.get("allow_sensitive_embeddings", False)):
        raise ValueError("LAN embedding requests require ollama.allow_sensitive_embeddings: true")
    response = requests.post(
        f"{endpoint}/api/embed",
        json={"model": config.embedding_model, "input": text},
        timeout=float(settings.get("timeout_seconds") or 180),
        allow_redirects=False,
    )
    response.raise_for_status()
    payload = response.json()
    embeddings = payload.get("embeddings") or []
    if not embeddings or not isinstance(embeddings[0], list):
        raise ValueError("Ollama returned no embedding")
    vector = [float(value) for value in embeddings[0]]
    magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / magnitude for value in vector]


def _embed(text: str, config: AppConfig) -> list[float]:
    return ollama_embedding(text, config) if config.embedding_backend == "ollama" else hash_embedding(text)


def _connect(database: Path) -> sqlite3.Connection:
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS media (path TEXT PRIMARY KEY, text TEXT NOT NULL, vector TEXT NOT NULL, metadata TEXT NOT NULL, indexed_at TEXT NOT NULL)"
    )
    return connection


def build_search_index(input_directory: Path, config: AppConfig, recursive: bool = True) -> dict[str, int]:
    indexed = failed = 0
    seen: set[str] = set()
    with _connect(config.search_database) as connection:
        for path in scan_images(input_directory, recursive=recursive):
            try:
                metadata = extract_metadata(path)
                text = _text(path, metadata)
                vector = _embed(text, config)
                connection.execute(
                    "INSERT OR REPLACE INTO media(path, text, vector, metadata, indexed_at) VALUES(?,?,?,?,?)",
                    (
                        str(path.resolve()),
                        text,
                        json.dumps(vector),
                        json.dumps(metadata, default=str),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                seen.add(str(path.resolve()))
                indexed += 1
            except Exception:
                failed += 1
        root = input_directory.resolve()
        stale = []
        for (stored_path,) in connection.execute("SELECT path FROM media"):
            path = Path(stored_path)
            try:
                path.relative_to(root)
            except ValueError:
                continue
            if stored_path not in seen:
                stale.append(stored_path)
        connection.executemany("DELETE FROM media WHERE path = ?", [(path,) for path in stale])
    return {"indexed": indexed, "failed": failed, "removed": len(stale)}


def search_index(query: str, config: AppConfig, limit: int = 20) -> list[dict[str, Any]]:
    query_vector = _embed(query, config)
    results: list[dict[str, Any]] = []
    with _connect(config.search_database) as connection:
        for path, text, vector_json, metadata_json in connection.execute("SELECT path, text, vector, metadata FROM media"):
            vector = json.loads(vector_json)
            score = sum(left * right for left, right in zip(query_vector, vector, strict=False))
            results.append({"path": path, "score": round(score, 6), "text": text, "metadata": json.loads(metadata_json)})
    return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]
