from __future__ import annotations

import time
import threading
from typing import List, Optional, Dict, Set

from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

from blackbox.settings import MatchSettings
from blackbox.utils.paths import templates_dir
from blackbox.vision.templates import load_templates, Template
from blackbox.vision.match import preprocess_frame, match_templates
from blackbox.vision.nms import nms
from blackbox.capture.screen import grab_region, Rect
from blackbox.ui.overlay_boxes import BoxesOverlay, Box
from blackbox.ui.sidebar import Sidebar
from blackbox.vision.tracker import StableTracker, Track
from blackbox.catalog import default_catalog
from blackbox.hotkeys.hotkey_manager import HotkeyManager


class DetectionWorker(QObject):
    """Background worker for template matching - keeps UI responsive."""
    results_ready = pyqtSignal(list)  # Emits List[Track]
    
    def __init__(self, templates: Dict[str, Template], settings: MatchSettings, region: Rect):
        super().__init__()
        self.templates = templates
        self.settings = settings
        self.region = region
        self.tracker = StableTracker(
            iou_threshold=settings.track_iou_threshold,
            ttl_seconds=settings.track_ttl_seconds
        )
        self._lock = threading.Lock()
        self._running = False
        self._threshold = 0.86
        self._selected_labels: Set[str] = set()
    
    def set_params(self, threshold: float, selected_labels: Set[str]):
        """Thread-safe parameter update from main thread."""
        with self._lock:
            self._threshold = threshold
            self._selected_labels = selected_labels.copy()
    
    def process_frame(self):
        """Run detection in background thread, emit results when done."""
        if self._running:
            return  # Skip if previous frame still processing
        
        with self._lock:
            threshold = self._threshold
            selected_labels = self._selected_labels.copy()
        
        if not selected_labels:
            self.results_ready.emit([])
            return
        
        self._running = True
        
        def _worker():
            try:
                bgr = grab_region(self.region)
                frame_data = preprocess_frame(bgr)
                
                active_templates = {k: v for k, v in self.templates.items() if k in selected_labels}
                
                strong_raw = match_templates(frame_data, active_templates, threshold=threshold)
                weak_raw = match_templates(frame_data, active_templates, threshold=max(0.55, threshold - 0.15))
                
                strong = nms(strong_raw, iou_threshold=self.settings.nms_iou_threshold)
                weak = nms(weak_raw, iou_threshold=self.settings.nms_iou_threshold)
                
                tracks = self.tracker.update(strong_dets=strong, weak_dets=weak)
                
                self.results_ready.emit(list(tracks))
            finally:
                self._running = False
        
        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()


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

    hotkey_mgr.register_hotkey(1, "<alt>+b", lambda: bridge.toggle_sidebar.emit())
    hotkey_mgr.register_hotkey(2, "<ctrl>+<alt>+b", lambda: bridge.toggle_sidebar.emit())

    import platform
    if platform.system() == "Darwin":
        hotkey_mgr.register_hotkey(3, "<cmd>+b", lambda: bridge.toggle_sidebar.emit())

    # Detection setup
    settings = MatchSettings()
    templates = load_templates(templates_dir())
    region = Rect(left=200, top=150, width=1700, height=1100)
    
    # Background detection worker
    worker = DetectionWorker(templates, settings, region)
    
    def on_results(tracks: List[Track]):
        """Handle detection results on main thread."""
        if not sidebar.enable_overlay.isChecked():
            overlay.update_boxes([])
            return
        
        boxes = []
        for tr in tracks:
            x, y = tr.x, tr.y
            x += region.left
            y += region.top
            boxes.append(Box(x=x, y=y, w=tr.w, h=tr.h, label=tr.label, confidence=tr.confidence))
        
        overlay.update_boxes(boxes)
    
    worker.results_ready.connect(on_results)

    target_fps = 12.0
    interval_ms = int(1000 / target_fps)

    def tick():
        # Update worker params and trigger processing
        threshold = sidebar.threshold_slider.value() / 100.0
        selected_labels = sidebar.selected_template_labels()
        
        worker.set_params(threshold, selected_labels)
        worker.process_frame()

    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(interval_ms)

    try:
        return app.exec()
    finally:
        hotkey_mgr.unregister_all()


if __name__ == "__main__":
    raise SystemExit(main())
