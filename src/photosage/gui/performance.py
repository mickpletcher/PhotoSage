from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image


class ThumbnailCache:
    def __init__(self, cache_directory: Path, size: int = 128) -> None:
        self.cache_directory = cache_directory
        self.size = size

    def thumbnail_for(self, image_path: Path) -> Path | None:
        self.cache_directory.mkdir(parents=True, exist_ok=True)
        output = self.cache_directory / f"{image_path.resolve().as_posix().replace('/', '_').replace(':', '')}_{self.size}.jpg"
        if output.exists() and output.stat().st_mtime >= image_path.stat().st_mtime:
            return output
        try:
            with Image.open(image_path) as image:
                image.thumbnail((self.size, self.size))
                image.convert("RGB").save(output, "JPEG", quality=85)
        except Exception:
            return None
        return output


def save_profile(profile_directory: Path, name: str, settings: dict[str, Any]) -> Path:
    profile_directory.mkdir(parents=True, exist_ok=True)
    path = profile_directory / f"{name}.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2, default=str)
    return path


def load_profile(profile_directory: Path, name: str) -> dict[str, Any]:
    path = profile_directory / f"{name}.json"
    with path.open("r", encoding="utf-8") as handle:
        return dict(json.load(handle))


def add_recent_manifest(recent_file: Path, manifest_path: Path, limit: int = 10) -> list[str]:
    recent_file.parent.mkdir(parents=True, exist_ok=True)
    manifests: list[str] = []
    if recent_file.exists():
        try:
            manifests = list(json.loads(recent_file.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, TypeError):
            manifests = []
    resolved = str(manifest_path.resolve())
    manifests = [resolved] + [path for path in manifests if path != resolved]
    manifests = manifests[:limit]
    recent_file.write_text(json.dumps(manifests, indent=2), encoding="utf-8")
    return manifests


def recent_manifests(recent_file: Path) -> list[Path]:
    if not recent_file.exists():
        return []
    try:
        return [Path(path) for path in json.loads(recent_file.read_text(encoding="utf-8"))]
    except (json.JSONDecodeError, TypeError):
        return []
