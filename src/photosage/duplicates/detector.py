from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, cast

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
            pixels = [cast(int, grayscale.getpixel((x, y))) for y in range(hash_size) for x in range(hash_size)]
    except Exception as error:
        logger.warning("duplicate hash skipped path=%s error=%s", image_path, error)
        return None

    average = sum(pixels) / len(pixels)
    bits = "".join("1" if pixel >= average else "0" for pixel in pixels)
    return f"{int(bits, 2):0{hash_size * hash_size // 4}x}"


def hamming_distance(left: str, right: str) -> int:
    return (int(left, 16) ^ int(right, 16)).bit_count()


class _BKNode:
    def __init__(self, image_hash: str, index: int) -> None:
        self.image_hash = image_hash
        self.indices = [index]
        self.children: dict[int, _BKNode] = {}

    def add(self, image_hash: str, index: int) -> None:
        distance = hamming_distance(self.image_hash, image_hash)
        if distance == 0:
            self.indices.append(index)
            return
        child = self.children.get(distance)
        if child:
            child.add(image_hash, index)
        else:
            self.children[distance] = _BKNode(image_hash, index)

    def search(self, image_hash: str, max_distance: int) -> list[int]:
        distance = hamming_distance(self.image_hash, image_hash)
        matches = list(self.indices) if distance <= max_distance else []
        lower = distance - max_distance
        upper = distance + max_distance
        for edge, child in self.children.items():
            if lower <= edge <= upper:
                matches.extend(child.search(image_hash, max_distance))
        return matches


def _find(parent: list[int], index: int) -> int:
    while parent[index] != index:
        parent[index] = parent[parent[index]]
        index = parent[index]
    return index


def _union(parent: list[int], left: int, right: int) -> None:
    left_root = _find(parent, left)
    right_root = _find(parent, right)
    if left_root != right_root:
        parent[right_root] = left_root


def find_duplicate_groups(image_paths: Iterable[Path], max_distance: int = 5) -> list[DuplicateGroup]:
    hashes: list[tuple[Path, str]] = []
    for path in image_paths:
        image_hash = average_hash(path)
        if image_hash:
            hashes.append((path.resolve(), image_hash))

    if not hashes:
        return []

    parent = list(range(len(hashes)))
    tree: _BKNode | None = None
    for index, (_, image_hash) in enumerate(hashes):
        if tree is None:
            tree = _BKNode(image_hash, index)
            continue
        for match_index in tree.search(image_hash, max_distance):
            _union(parent, index, match_index)
        tree.add(image_hash, index)

    components: dict[int, list[int]] = {}
    for index in range(len(hashes)):
        components.setdefault(_find(parent, index), []).append(index)

    groups: list[DuplicateGroup] = []
    for indices in sorted((value for value in components.values() if len(value) > 1), key=lambda value: value[0]):
        reference_hash = hashes[indices[0]][1]
        groups.append(
            DuplicateGroup(
                group_id=f"dup-{len(groups) + 1:04d}",
                hash=reference_hash,
                files=[str(hashes[index][0]) for index in indices],
                distance=max(hamming_distance(reference_hash, hashes[index][1]) for index in indices),
            )
        )
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
