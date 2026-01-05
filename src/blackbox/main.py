from __future__ import annotations

import time

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from blackbox.settings import MatchSettings
from blackbox.utils.paths import templates_dir
from blackbox.vision.templates import load_templates
from blackbox.vision.match import preprocess_frame, match_templates
from blackbox.vision.nms import nms
from blackbox.capture.screen import grab_region, Rect
from blackbox.ui.overlay import OverlayWindow, Box
from blackbox.vision.tracker import StableTracker


def main() -> int:
    settings = MatchSettings()
    templates = load_templates(templates_dir())

    # If you want full-screen scan, keep region = None.
    # If you want only Rust area, set Rect(...) and ALSO offset boxes (see note below).
    region = None
    # region = Rect(left=0, top=0, width=1920, height=1080)

    app = QApplication([])

    overlay = OverlayWindow()

    target_fps = 10.0
    interval_ms = int(1000 / target_fps)

    tracker = StableTracker(
        iou_threshold=settings.track_iou_threshold,
        ttl_seconds=settings.track_ttl_seconds
    )


    def tick():
        bgr = grab_region(region)
        gray = preprocess_frame(bgr)

        raw_strong = match_templates(gray, templates, threshold=settings.threshold)
        raw_weak   = match_templates(gray, templates, threshold=settings.keep_threshold)

        strong = nms(raw_strong, iou_threshold=settings.nms_iou_threshold)
        weak   = nms(raw_weak,   iou_threshold=settings.nms_iou_threshold)

        tracks = tracker.update(strong_dets=strong, weak_dets=weak)


        # raw = match_templates(gray, templates, threshold=settings.threshold)
        # filtered = nms(raw, iou_threshold=settings.nms_iou_threshold)
        # tracks = tracker.update(filtered)

        # Convert matches -> overlay boxes
        boxes = []
        for tr in tracks:
            x, y = tr.x, tr.y
            if region is not None:
                x += region.left
                y += region.top
            boxes.append(Box(x=x, y=y, w=tr.w, h=tr.h, label=tr.label, confidence=tr.confidence))

        overlay.update_boxes(boxes)

    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(interval_ms)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
