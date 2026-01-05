from __future__ import annotations

from dataclasses import dataclass
from typing import List

from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtWidgets import QApplication, QWidget

from blackbox.capture.screen import Rect

@dataclass(frozen=True)
class Box:
    x: int
    y: int
    w: int
    h: int
    label: str = ""
    confidence: float = 0.0


class BoxesOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self._boxes: List[Box] = []
        self._roi: Rect | None = None
        self._show_roi: bool = True

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Make click-through for input
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        screen = QApplication.primaryScreen()
        geo = screen.geometry()
        self.setGeometry(geo)
        self.show()

    def update_boxes(self, boxes: List[Box]) -> None:
        self._boxes = boxes
        self.update()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # --- Draw ROI rectangle (scan region) ---
        if self._show_roi and self._roi is not None:
            roi_pen = QPen()
            roi_pen.setWidth(3)
            roi_pen.setStyle(Qt.PenStyle.DashLine)
            roi_pen.setColor(Qt.GlobalColor.yellow)
            painter.setPen(roi_pen)
            painter.drawRect(QRect(self._roi.left, self._roi.top, self._roi.width, self._roi.height))

        # --- Draw detected boxes ---
        box_pen = QPen()
        box_pen.setWidth(3)
        box_pen.setColor(Qt.GlobalColor.green)
        painter.setPen(box_pen)

        for b in self._boxes:
            painter.drawRect(QRect(b.x, b.y, b.w, b.h))
    
    def set_roi(self, roi: Rect | None) -> None:
        self._roi = roi
        self.update()

    def set_show_roi(self, show: bool) -> None:
        self._show_roi = show
        self.update()

