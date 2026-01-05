from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import mss
import numpy as np
import cv2


@dataclass(frozen=True)
class Rect:
    left: int
    top: int
    width: int
    height: int


def grab_region(region: Optional[Rect] = None) -> np.ndarray:
    """
    Capture a region of the screen and return a BGR image (OpenCV format).
    If region is None, captures primary monitor.
    """
    with mss.mss() as sct:
        if region is None:
            mon = sct.monitors[1]  # primary monitor
            bbox = {"left": mon["left"], "top": mon["top"], "width": mon["width"], "height": mon["height"]}
        else:
            bbox = {"left": region.left, "top": region.top, "width": region.width, "height": region.height}

        shot = sct.grab(bbox)
        img = np.array(shot)               # BGRA
        bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return bgr
