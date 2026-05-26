from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from PIL import Image

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DuplicateGroup:
    group_id: str
    hash: str
    files: list[str]
    distance: int

    def to_dict(self) -> dict:
        return asdict(self)


def average_hash(image_path: Path, hash_size: int = 8) -> str | None:
    try:
        with Image.open(image_path) as image:
            grayscale = image.convert("L").resize((hash_size, hash_size))
            if hasattr(grayscale, "get_flattened_data"):
                pixels = list(grayscale.get_flattened_data())
            else:
                pixels = list(grayscale.getdata())
    except Exception as error:
        logger.warning("duplicate hash skipped path=%s error=%s", image_path, error)
        return None

    average = sum(pixels) / len(pixels)
    bits = "".join("1" if pixel >= average else "0" for pixel in pixels)
    return f"{int(bits, 2):0{hash_size * hash_size // 4}x}"


def hamming_distance(left: str, right: str) -> int:
    return (int(left, 16) ^ int(right, 16)).bit_count()


def find_duplicate_groups(image_paths: Iterable[Path], max_distance: int = 5) -> list[DuplicateGroup]:
    hashes: list[tuple[Path, str]] = []
    for path in image_paths:
        image_hash = average_hash(path)
        if image_hash:
            hashes.append((path.resolve(), image_hash))

    grouped: set[Path] = set()
    groups: list[DuplicateGroup] = []
    group_number = 1
    for path, image_hash in hashes:
        if path in grouped:
            continue
        matches = [(path, image_hash, 0)]
        for candidate_path, candidate_hash in hashes:
            if candidate_path == path or candidate_path in grouped:
                continue
            distance = hamming_distance(image_hash, candidate_hash)
            if distance <= max_distance:
                matches.append((candidate_path, candidate_hash, distance))

        if len(matches) < 2:
            continue

        for match_path, _, _ in matches:
            grouped.add(match_path)
        groups.append(
            DuplicateGroup(
                group_id=f"dup-{group_number:04d}",
                hash=image_hash,
                files=[str(match_path) for match_path, _, _ in matches],
                distance=max(distance for _, _, distance in matches),
            )
        )
        group_number += 1
    return groups


def duplicate_index(groups: list[DuplicateGroup]) -> dict[str, dict[str, str | int]]:
    index: dict[str, dict[str, str | int]] = {}
    for group in groups:
        for file_path in group.files:
            index[str(Path(file_path).resolve())] = {
                "duplicate_group_id": group.group_id,
                "duplicate_hash": group.hash,
                "duplicate_distance": group.distance,
            }
    return index


def write_duplicate_report(groups: list[DuplicateGroup], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "groups": [group.to_dict() for group in groups],
    }
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return output_path
