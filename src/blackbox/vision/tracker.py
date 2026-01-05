from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import time

from blackbox.vision.match import Match


@dataclass(frozen=True)
class Track:
    id: int
    label: str
    x: int
    y: int
    w: int
    h: int
    confidence: float
    last_seen: float


def _iou_xywh(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax1, ay1, ax2, ay2 = ax, ay, ax + aw, ay + ah
    bx1, by1, bx2, by2 = bx, by, bx + bw, by + bh

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    iw = max(0, inter_x2 - inter_x1)
    ih = max(0, inter_y2 - inter_y1)
    inter = iw * ih
    if inter <= 0:
        return 0.0

    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


class StableTracker:
    """
    Tracking-by-detection with hysteresis:
    - strong detections create new tracks
    - weak detections refresh existing tracks
    - tracks persist for ttl_seconds after last refresh
    """
    def __init__(self, iou_threshold: float = 0.3, ttl_seconds: float = 1.5):
        self.iou_threshold = iou_threshold
        self.ttl_seconds = ttl_seconds
        self._next_id = 1
        self._tracks: Dict[int, Track] = {}

    def _best_match(self, tr: Track, dets: List[Match], used: set[int]) -> Optional[int]:
        best_j = None
        best_iou = 0.0
        tr_box = (tr.x, tr.y, tr.w, tr.h)

        for j, d in enumerate(dets):
            if j in used:
                continue
            if d.label != tr.label:
                continue
            iou = _iou_xywh(tr_box, (d.x, d.y, d.w, d.h))
            if iou > best_iou:
                best_iou = iou
                best_j = j

        if best_j is not None and best_iou >= self.iou_threshold:
            return best_j
        return None

    def update(
        self,
        strong_dets: List[Match],
        weak_dets: List[Match],
        now: Optional[float] = None,
    ) -> List[Track]:
        if now is None:
            now = time.time()

        # 1) Refresh existing tracks using WEAK detections (prevents flicker)
        used_weak: set[int] = set()
        refreshed: Dict[int, Track] = {}

        for tid, tr in self._tracks.items():
            j = self._best_match(tr, weak_dets, used_weak)
            if j is not None:
                d = weak_dets[j]
                used_weak.add(j)
                refreshed[tid] = Track(
                    id=tid, label=tr.label,
                    x=d.x, y=d.y, w=d.w, h=d.h,
                    confidence=d.confidence,
                    last_seen=now,
                )
            else:
                # Keep track as-is (may expire later)
                refreshed[tid] = tr

        # 2) Create new tracks from STRONG detections that don't match any existing track
        # Prevent creating duplicates near existing tracks
        def overlaps_existing(d: Match) -> bool:
            d_box = (d.x, d.y, d.w, d.h)
            for tr in refreshed.values():
                if tr.label != d.label:
                    continue
                if _iou_xywh((tr.x, tr.y, tr.w, tr.h), d_box) >= self.iou_threshold:
                    return True
            return False

        for d in strong_dets:
            if overlaps_existing(d):
                continue
            tid = self._next_id
            self._next_id += 1
            refreshed[tid] = Track(
                id=tid, label=d.label,
                x=d.x, y=d.y, w=d.w, h=d.h,
                confidence=d.confidence,
                last_seen=now,
            )

        # 3) Expire old tracks
        alive: Dict[int, Track] = {}
        for tid, tr in refreshed.items():
            if (now - tr.last_seen) <= self.ttl_seconds:
                alive[tid] = tr

        self._tracks = alive
        return list(self._tracks.values())
