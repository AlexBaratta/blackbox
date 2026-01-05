from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import cv2
import numpy as np


@dataclass(frozen=True)
class Template:
    label: str
    img_gray: np.ndarray  # grayscale template image


def load_templates(dir_path: Path) -> Dict[str, Template]:
    if not dir_path.exists():
        raise RuntimeError(f"Templates directory not found: {dir_path}")

    templates: Dict[str, Template] = {}
    for p in sorted(dir_path.glob("*.png")):
        label = p.stem.upper()
        img = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise RuntimeError(f"Failed to load template image: {p}")
        templates[label] = Template(label=label, img_gray=img)

    if not templates:
        raise RuntimeError(f"No .png templates found in: {dir_path}")

    return templates
