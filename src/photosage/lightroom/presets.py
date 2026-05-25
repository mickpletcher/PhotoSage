from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LightroomPreset:
    """Lightroom workflow preset."""

    name: str
    metadata_threshold: int
    filename_format: str
    organize: bool
    force_ai: bool
    category: str | None = None


PRESETS: dict[str, LightroomPreset] = {
    "documentary": LightroomPreset("documentary", 75, "{date}_{location}_{subject}_{context}_{counter}", True, False, None),
    "travel": LightroomPreset("travel", 70, "{date}_{location}_{subject}_{context}_{counter}", True, False, "Travel"),
    "astronomy": LightroomPreset("astronomy", 65, "{date}_{subject}_{context}_{counter}", True, False, "Astrophotography"),
    "wildlife": LightroomPreset("wildlife", 70, "{date}_{location}_{subject}_{counter}", True, False, "Wildlife"),
    "construction": LightroomPreset("construction", 70, "{date}_{location}_{subject}_{context}_{counter}", True, False, "Construction"),
    "family": LightroomPreset("family", 80, "{date}_{location}_{subject}_{counter}", True, False, "Family"),
    "minimalist": LightroomPreset("minimalist", 80, "{date}_{subject}_{counter}", False, False, None),
    "metadata-only": LightroomPreset("metadata-only", 60, "{date}_{location}_{subject}_{counter}", False, False, None),
    "ai-heavy": LightroomPreset("ai-heavy", 90, "{date}_{location}_{subject}_{context}_{counter}", True, True, None),
}


def get_preset(name: str | None) -> LightroomPreset | None:
    """Return a preset by name."""
    if not name:
        return None
    return PRESETS.get(name.lower())

