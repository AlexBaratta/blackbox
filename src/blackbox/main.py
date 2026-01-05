from __future__ import annotations

import time

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QAbstractNativeEventFilter

from blackbox.settings import MatchSettings
from blackbox.utils.paths import templates_dir
from blackbox.vision.templates import load_templates
from blackbox.vision.match import preprocess_frame, match_templates
from blackbox.vision.nms import nms
from blackbox.capture.screen import grab_region, Rect
from blackbox.ui.overlay_boxes import BoxesOverlay, Box
from blackbox.ui.sidebar import Sidebar
from blackbox.hotkeys.win_hotkey import HotkeyManager
from blackbox.vision.tracker import StableTracker  # your “solid boxes” tracker


class NativeEventFilter(QAbstractNativeEventFilter):
    def __init__(self, hotkeys: HotkeyManager):
        super().__init__()
        self.hotkeys = hotkeys

    def nativeEventFilter(self, event_type, message):
        handled = self.hotkeys.handle_native_event(event_type, message)
        return handled, 0



def main() -> int:
    app = QApplication([])

    # UI
    overlay = BoxesOverlay()
    sidebar = Sidebar()

    # Hotkey
    hotkeys = HotkeyManager()
    hotkeys.register_alt_b(hotkey_id=1, callback=sidebar.toggle)

    # Native event hook
    filt = NativeEventFilter(hotkeys)
    app.installNativeEventFilter(filt)

    # Detection setup
    settings = MatchSettings()
    templates = load_templates(templates_dir())

    tracker = StableTracker(
        iou_threshold=settings.track_iou_threshold,
        ttl_seconds=settings.track_ttl_seconds
    )

    region = None  # full screen
    target_fps = 10.0
    interval_ms = int(1000 / target_fps)

    def tick():
        # Read sidebar threshold live
        settings_threshold = sidebar.threshold_slider.value() / 100.0

        bgr = grab_region(region)
        gray = preprocess_frame(bgr)

        # Hysteresis: strong/weak
        strong_raw = match_templates(gray, templates, threshold=settings_threshold)
        weak_raw = match_templates(gray, templates, threshold=max(0.60, settings_threshold - 0.12))

        strong = nms(strong_raw, iou_threshold=settings.nms_iou_threshold)
        weak = nms(weak_raw, iou_threshold=settings.nms_iou_threshold)

        tracks = tracker.update(strong_dets=strong, weak_dets=weak)

        if not sidebar.enable_overlay.isChecked():
            overlay.update_boxes([])
            return

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

    try:
        return app.exec()
    finally:
        hotkeys.unregister_all()


if __name__ == "__main__":
    raise SystemExit(main())
