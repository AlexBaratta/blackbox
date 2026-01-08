from __future__ import annotations

from dataclasses import dataclass
from typing import List

from PyQt6.QtCore import Qt, QRect, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QBrush
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

        # --- Draw detected boxes with labels ---
        box_pen = QPen()
        box_pen.setWidth(3)
        box_pen.setColor(QColor(0, 255, 100))  # Bright green
        painter.setPen(box_pen)

        # Font for labels
        font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        painter.setFont(font)

        for b in self._boxes:
            # Draw box outline
            painter.setPen(box_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRect(b.x, b.y, b.w, b.h))
            
            # Draw label with dark background
            if b.label:
                label_text = f"{b.label}"
                
                # Measure text
                metrics = painter.fontMetrics()
                text_width = metrics.horizontalAdvance(label_text)
                text_height = metrics.height()
                
                # Label position (above the box)
                padding_x = 6
                padding_y = 4
                label_x = b.x
                label_y = b.y - text_height - padding_y * 2 - 4
                
                # If label would go off screen top, put it below
                if label_y < 0:
                    label_y = b.y + b.h + 4
                
                # Draw dark background rectangle
                bg_rect = QRectF(
                    label_x, 
                    label_y, 
                    text_width + padding_x * 2, 
                    text_height + padding_y * 2
                )
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(20, 20, 20, 220)))  # Dark semi-transparent
                painter.drawRoundedRect(bg_rect, 4, 4)
                
                # Draw text
                painter.setPen(QColor(0, 255, 100))  # Bright green text
                painter.drawText(
                    int(label_x + padding_x), 
                    int(label_y + padding_y + metrics.ascent()), 
                    label_text
                )
    
    def set_roi(self, roi: Rect | None) -> None:
        self._roi = roi
        self.update()

    def set_show_roi(self, show: bool) -> None:
        self._show_roi = show
        self.update()

