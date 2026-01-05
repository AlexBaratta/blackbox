from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import cv2
import numpy as np

from blackbox.vision.templates import Template


@dataclass(frozen=True)
class Match:
    label: str
    confidence: float
    x: int
    y: int
    w: int
    h: int


def preprocess_frame(bgr: np.ndarray) -> np.ndarray:
    """
    Preprocess the screenshot for template matching.
    Keep it light; we can tune later.
    """
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    return gray


def match_templates(
    frame_gray: np.ndarray,
    templates: Dict[str, Template],
    threshold: float,
) -> List[Match]:
    matches: List[Match] = []

    for label, tpl in templates.items():
        th, tw = tpl.img_gray.shape[:2]

        # Normalized correlation coefficient
        res = cv2.matchTemplate(frame_gray, tpl.img_gray, cv2.TM_CCOEFF_NORMED)

        ys, xs = np.where(res >= threshold)
        for x, y in zip(xs, ys):
            conf = float(res[y, x])
            matches.append(Match(label=label, confidence=conf, x=int(x), y=int(y), w=int(tw), h=int(th)))

    matches.sort(key=lambda m: m.confidence, reverse=True)
    return matches


def draw_matches(bgr: np.ndarray, matches: List[Match], max_draw: int = 80) -> np.ndarray:
    out = bgr.copy()
    for m in matches[:max_draw]:
        cv2.rectangle(out, (m.x, m.y), (m.x + m.w, m.y + m.h), (0, 255, 0), 2)
        cv2.putText(
            out,
            f"{m.label}:{m.confidence:.2f}",
            (m.x, max(20, m.y - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
    return out
