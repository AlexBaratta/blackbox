from __future__ import annotations

import sys
from pathlib import Path

import cv2

from blackbox.settings import MatchSettings
from blackbox.utils.paths import templates_dir, project_root
from blackbox.vision.templates import load_templates
from blackbox.vision.match import preprocess_frame, match_templates, draw_matches
from blackbox.vision.nms import nms


def main() -> int:
    settings = MatchSettings()

    if len(sys.argv) < 2:
        print("Usage: python -m blackbox.main <path_to_image>")
        return 2

    img_path = Path(sys.argv[1])
    if not img_path.exists():
        print(f"File not found: {img_path}")
        return 2

    bgr = cv2.imread(str(img_path))
    if bgr is None:
        print("Failed to load image.")
        return 2

    tpls = load_templates(templates_dir())
    frame_gray = preprocess_frame(bgr)

    raw = match_templates(frame_gray, tpls, threshold=settings.threshold)
    filtered = nms(raw, iou_threshold=settings.nms_iou_threshold)

    print(f"Raw matches: {len(raw)} | After NMS: {len(filtered)}")
    print("Top 15:", filtered[:15])

    vis = draw_matches(bgr, filtered, max_draw=settings.max_debug_draw)
    cv2.imshow("Blackbox - template matches", vis)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
