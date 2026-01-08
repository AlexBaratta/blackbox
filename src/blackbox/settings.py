from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MatchSettings:
    # Template match threshold (0..1). Raise to reduce false positives.
    threshold: float = 0.85
    
    # Lower threshold for keeping/refreshing existing tracks (hysteresis)
    keep_threshold: float = 0.72
    
    # How many matches to draw in debug output
    max_debug_draw: int = 80

    # NMS: if two boxes overlap more than this, keep only the best
    # Lower = allow more adjacent detections, Higher = more aggressive merging
    nms_iou_threshold: float = 0.25  # Lowered to allow adjacent same items
    
    # Tracker settings
    track_iou_threshold: float = 0.30  # Match threshold for tracking
    track_ttl_seconds: float = 1.2     # How long tracks persist without detection (longer = less flicker)
