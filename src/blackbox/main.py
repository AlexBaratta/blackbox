from __future__ import annotations

import time

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

from blackbox.settings import MatchSettings
from blackbox.utils.paths import templates_dir
from blackbox.vision.templates import load_templates
from blackbox.vision.match import preprocess_frame, match_templates
from blackbox.vision.nms import nms
from blackbox.capture.screen import grab_region, Rect
from blackbox.ui.overlay_boxes import BoxesOverlay, Box
from blackbox.ui.sidebar import Sidebar
# from blackbox.hotkeys.win_hotkey import HotkeyManager
from blackbox.vision.tracker import StableTracker 
from blackbox.catalog import default_catalog
from blackbox.hotkeys.hotkey_manager import HotkeyManager

class UiBridge(QObject):
    toggle_sidebar = pyqtSignal()

    def __init__(self, sidebar):
        super().__init__()
        self.toggle_sidebar.connect(lambda: (print("HOTKEY FIRED"), sidebar.toggle()))



def main() -> int:
    app = QApplication([])

    # UI
    overlay = BoxesOverlay()
    catalog = default_catalog()
    sidebar = Sidebar(catalog)


    # Hotkey
    bridge = UiBridge(sidebar)
    hotkey_mgr = HotkeyManager()

    # Windows: Alt+B (may be swallowed by some games)
    hotkey_mgr.register_hotkey(1, "<alt>+b", lambda: bridge.toggle_sidebar.emit())

    # Windows fallback that is usually reliable even in games:
    hotkey_mgr.register_hotkey(2, "<ctrl>+<alt>+b", lambda: bridge.toggle_sidebar.emit())

    import platform
    if platform.system() == "Darwin":
        # macOS: Cmd+B
        hotkey_mgr.register_hotkey(3, "<cmd>+b", lambda: bridge.toggle_sidebar.emit())


    # Native event hook

    # Detection setup
    settings = MatchSettings()
    templates = load_templates(templates_dir())

    tracker = StableTracker(
        iou_threshold=settings.track_iou_threshold,
        ttl_seconds=settings.track_ttl_seconds
    )

    region = Rect(left=200, top=150, width=1700, height=1100)
    # overlay.set_roi(region)
    # overlay.set_show_roi(True)

    target_fps = 10.0
    interval_ms = int(1000 / target_fps)

    def tick():
        # Read sidebar threshold live
        settings_threshold = sidebar.threshold_slider.value() / 100.0

        bgr = grab_region(region)
        frame_data = preprocess_frame(bgr)  # Returns (gray, bgr) tuple

        selected_labels = sidebar.selected_template_labels()

        if not selected_labels:
            overlay.update_boxes([])
            return

        active_templates = {k: v for k, v in templates.items() if k in selected_labels}
        
        # Hysteresis: strong/weak - grayscale matching + color verification
        strong_raw = match_templates(frame_data, active_templates, threshold=settings_threshold)
        weak_raw = match_templates(frame_data, active_templates, threshold=max(0.55, settings_threshold - 0.15))

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
        hotkey_mgr.unregister_all()


if __name__ == "__main__":
    raise SystemExit(main())
