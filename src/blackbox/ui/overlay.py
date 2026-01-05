from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtWidgets import QApplication, QWidget


@dataclass(frozen=True)
class Box:
    x: int
    y: int
    w: int
    h: int
    label: str = ""
    confidence: float = 0.0


class OverlayWindow(QWidget):
    """
    Fullscreen transparent window that draws rectangles.
    Note: true click-through requires extra Win32 calls; this is a good baseline first.
    """
    def __init__(self):
        super().__init__()
        self._boxes: List[Box] = []

        # Transparent, borderless, always on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Fullscreen on primary display
        screen = QApplication.primaryScreen()
        geo = screen.geometry()
        self.setGeometry(geo)

        self.show()

    def update_boxes(self, boxes: List[Box]) -> None:
        self._boxes = boxes
        self.update()  # trigger repaint

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        pen = QPen()
        pen.setWidth(3)
        pen.setColor(Qt.GlobalColor.green)
        painter.setPen(pen)

        for b in self._boxes:
            painter.drawRect(QRect(b.x, b.y, b.w, b.h))
