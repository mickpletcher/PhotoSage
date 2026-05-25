from __future__ import annotations

from pathlib import Path
from typing import Callable


def unique_destination(
    directory: Path,
    build_name: Callable[[int], str],
    seen: set[Path] | None = None,
) -> Path:
    """Return the first destination path that will not overwrite a file."""
    seen = seen if seen is not None else set()
    counter = 1
    while True:
        candidate = directory / build_name(counter)
        resolved = candidate.resolve()
        if not candidate.exists() and resolved not in seen:
            seen.add(resolved)
            return candidate
        counter += 1

