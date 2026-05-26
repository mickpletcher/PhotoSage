from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class GeocodeCache:
    def __init__(self, cache_path: Path, ttl_days: int = 365, aliases: dict[str, str] | None = None) -> None:
        self.cache_path = cache_path
        self.ttl = timedelta(days=ttl_days)
        self.aliases = aliases or {}
        self.data = self._load()

    def resolve(self, latitude: float | None, longitude: float | None) -> str | None:
        if latitude is None or longitude is None:
            return None
        key = self.key(latitude, longitude)
        if key in self.aliases:
            return self.aliases[key]
        entry = self.data.get(key)
        if not entry:
            return None
        timestamp = datetime.fromisoformat(entry["timestamp"])
        if datetime.now(timezone.utc) - timestamp > self.ttl:
            return None
        return str(entry["location"])

    def set(self, latitude: float, longitude: float, location: str) -> None:
        self.data[self.key(latitude, longitude)] = {
            "location": location,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.save()

    def save(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_path.open("w", encoding="utf-8") as handle:
            json.dump(self.data, handle, indent=2)

    @staticmethod
    def key(latitude: float, longitude: float) -> str:
        return f"{latitude:.5f},{longitude:.5f}"

    def _load(self) -> dict[str, Any]:
        if not self.cache_path.exists():
            return {}
        try:
            with self.cache_path.open("r", encoding="utf-8") as handle:
                return dict(json.load(handle))
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            return {}
