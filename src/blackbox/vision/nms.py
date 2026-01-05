from __future__ import annotations

from typing import List

from blackbox.vision.match import Match


def _iou(a: Match, b: Match) -> float:
    ax1, ay1, ax2, ay2 = a.x, a.y, a.x + a.w, a.y + a.h
    bx1, by1, bx2, by2 = b.x, b.y, b.x + b.w, b.y + b.h

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    iw = max(0, inter_x2 - inter_x1)
    ih = max(0, inter_y2 - inter_y1)
    inter = iw * ih
    if inter == 0:
        return 0.0

    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def nms(matches: List[Match], iou_threshold: float) -> List[Match]:
    """
    Simple greedy NMS:
    - Assume matches sorted by confidence (high → low)
    - Keep a match if it doesn't overlap too much with any kept box
    """
    kept: List[Match] = []
    for m in matches:
        if all(_iou(m, k) < iou_threshold for k in kept):
            kept.append(m)
    return kept
