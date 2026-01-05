from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QCheckBox, QPushButton


class Sidebar(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Basic sizing/position (right side)
        self.setFixedWidth(320)
        self._reposition_right()

        # Content container
        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        title = QLabel("Blackbox Settings")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: white;")
        layout.addWidget(title)

        self.enable_overlay = QCheckBox("Enable boxes overlay")
        self.enable_overlay.setChecked(True)
        self.enable_overlay.setStyleSheet("color: white;")
        layout.addWidget(self.enable_overlay)

        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(60)
        self.threshold_slider.setMaximum(95)
        self.threshold_slider.setValue(86)
        layout.addWidget(QLabel("Match threshold (0.60–0.95)"))
        layout.addWidget(self.threshold_slider)

        close_btn = QPushButton("Close (Alt+Z)")
        layout.addWidget(close_btn)
        close_btn.clicked.connect(self.hide)

        self.setLayout(layout)

        # Semi-transparent background via stylesheet
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 20, 200);
                border: 1px solid rgba(255,255,255,60);
                border-radius: 12px;
            }
            QLabel { color: white; }
            QPushButton {
                padding: 8px;
                border-radius: 10px;
                background-color: rgba(255,255,255,30);
                color: white;
            }
            QPushButton:hover { background-color: rgba(255,255,255,45); }
        """)

        self.hide()

    def _reposition_right(self):
        screen = self.screen()
        geo = screen.availableGeometry()
        # Right side, vertically centered-ish
        x = geo.x() + geo.width() - self.width() - 20
        y = geo.y() + 120
        self.move(x, y)

    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self._reposition_right()
            self.show()
            self.raise_()
            self.activateWindow()
