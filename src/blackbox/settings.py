from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MatchSettings:
    # Template match threshold (0..1). Raise to reduce false positives.
    threshold: float = 0.80

    # How many matches to draw in debug output (before NMS it can be a lot)
    max_debug_draw: int = 80

    # NMS: if two boxes overlap more than this, keep only the best
    nms_iou_threshold: float = 0.35
