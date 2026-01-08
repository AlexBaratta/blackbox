from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

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


def preprocess_frame(bgr: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Preprocess the screenshot for template matching.
    Returns (gray, bgr) tuple.
    """
    blurred = cv2.GaussianBlur(bgr, (3, 3), 0)
    gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
    return gray, blurred


def template_has_color(img_bgr: np.ndarray, threshold: float = 8.0) -> bool:
    """
    Check if template has significant color information.
    Grayscale/metallic items have low A/B channel variance.
    """
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    a_std = np.std(lab[:, :, 1])
    b_std = np.std(lab[:, :, 2])
    return (a_std + b_std) > threshold


def color_similarity(region_bgr: np.ndarray, template_bgr: np.ndarray, template_has_color_info: bool) -> float:
    """
    Compute color similarity between region and template.
    For colorful templates: use LAB color channels
    For grayscale templates: just return 1.0 (rely on grayscale matching)
    """
    if region_bgr.shape != template_bgr.shape:
        return 0.0
    
    # For grayscale/metallic templates, skip color check
    if not template_has_color_info:
        return 1.0
    
    # Convert to LAB
    region_lab = cv2.cvtColor(region_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    template_lab = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    
    # Only compare A and B channels (color), ignore L (luminance)
    region_ab = region_lab[:, :, 1:3].reshape(-1)
    template_ab = template_lab[:, :, 1:3].reshape(-1)
    
    # Mean Absolute Error - simpler and more stable than NCC
    mae = np.mean(np.abs(region_ab - template_ab))
    
    # Convert MAE to similarity (0-1 range, lower MAE = higher similarity)
    # Typical MAE range is 0-50 for different colors
    similarity = max(0.0, 1.0 - mae / 40.0)
    
    return similarity


def match_templates(
    frame_data: Tuple[np.ndarray, np.ndarray],
    templates: Dict[str, Template],
    threshold: float,
    color_weight: float = 0.30,  # How much color affects final score
) -> List[Match]:
    """
    Two-stage matching:
    1. Grayscale template matching (finds candidates)
    2. Color verification (for colorful templates only)
    
    Final score = (1 - color_weight) * gray_score + color_weight * color_score
    For grayscale templates, color_score = 1.0 (no penalty)
    """
    frame_gray, frame_bgr = frame_data
    matches: List[Match] = []

    for label, tpl in templates.items():
        th, tw = tpl.img_gray.shape[:2]
        has_color = tpl.has_color if hasattr(tpl, 'has_color') else template_has_color(tpl.img_bgr)

        # Stage 1: Grayscale matching
        res = cv2.matchTemplate(frame_gray, tpl.img_gray, cv2.TM_CCOEFF_NORMED)
        
        # Find candidates above search threshold
        search_threshold = max(0.55, threshold - 0.12)
        ys, xs = np.where(res >= search_threshold)
        
        for x, y in zip(xs, ys):
            gray_score = float(res[y, x])
            
            # Stage 2: Color verification (only for colorful templates)
            if tpl.img_bgr is not None:
                region = frame_bgr[y:y+th, x:x+tw]
                if region.shape[0] == th and region.shape[1] == tw:
                    color_score = color_similarity(region, tpl.img_bgr, has_color)
                    
                    # Combined score
                    if has_color:
                        final_score = (1 - color_weight) * gray_score + color_weight * color_score
                    else:
                        # Grayscale template - rely entirely on grayscale matching
                        final_score = gray_score
                else:
                    final_score = gray_score
            else:
                final_score = gray_score
            
            # Apply threshold to final score
            if final_score >= threshold:
                matches.append(Match(
                    label=label, 
                    confidence=final_score, 
                    x=int(x), y=int(y), w=int(tw), h=int(th)
                ))

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
