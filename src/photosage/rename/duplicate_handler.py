from __future__ import annotations

from pathlib import Path
from typing import Callable


def existing_names(directory: Path) -> set[str]:
    """Return lowercase filenames already present in a directory."""
    if not directory.exists():
        return set()
    return {path.name.lower() for path in directory.iterdir() if path.is_file()}


def unique_destination(
    directory: Path,
    build_name: Callable[[int], str],
    seen: set[Path] | None = None,
    existing: set[str] | None = None,
    original_path: Path | None = None,
) -> Path:
    """Return the first destination path that will not overwrite a file."""
    seen = seen if seen is not None else set()
    existing = existing if existing is not None else existing_names(directory)
    original_resolved = original_path.resolve() if original_path else None
    counter = 1
    while True:
        candidate = directory / build_name(counter)
        resolved = candidate.resolve()
        if original_resolved and resolved == original_resolved:
            seen.add(resolved)
            return candidate
        if candidate.name.lower() not in existing and resolved not in seen:
            seen.add(resolved)
            existing.add(candidate.name.lower())
            return candidate
        counter += 1
