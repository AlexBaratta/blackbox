from __future__ import annotations

from dataclasses import dataclass
from typing import List

from PyQt6.QtCore import Qt, QRect
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


class BoxesOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self._boxes: List[Box] = []

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

        pen = QPen()
        pen.setWidth(3)
        pen.setColor(Qt.GlobalColor.green)
        painter.setPen(pen)

        for b in self._boxes:
            painter.drawRect(QRect(b.x, b.y, b.w, b.h))
