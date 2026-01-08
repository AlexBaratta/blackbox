from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import cv2
import numpy as np


@dataclass(frozen=True)
class Template:
    label: str
    img_gray: np.ndarray  # grayscale template image
    img_bgr: Optional[np.ndarray] = None  # color template for color verification
    has_color: bool = True  # whether template has significant color info


def check_has_color(img_bgr: np.ndarray, threshold: float = 8.0) -> bool:
    """
    Check if template has significant color information.
    Grayscale/metallic items have low A/B channel variance in LAB space.
    """
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    a_std = np.std(lab[:, :, 1])
    b_std = np.std(lab[:, :, 2])
    return (a_std + b_std) > threshold


def load_templates(dir_path: Path) -> Dict[str, Template]:
    if not dir_path.exists():
        raise RuntimeError(f"Templates directory not found: {dir_path}")

    templates: Dict[str, Template] = {}
    for p in sorted(dir_path.glob("*.png")):
        label = p.stem.upper()
        
        # Load color image
        img_bgr = cv2.imread(str(p), cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise RuntimeError(f"Failed to load template image: {p}")
        
        img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        has_color = check_has_color(img_bgr)
        
        templates[label] = Template(label=label, img_gray=img_gray, img_bgr=img_bgr, has_color=has_color)

    if not templates:
        raise RuntimeError(f"No .png templates found in: {dir_path}")

    return templates
