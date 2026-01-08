from __future__ import annotations

from typing import Dict, List, Set

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSlider, QCheckBox, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem
)

from blackbox.catalog import CatalogItem


class Sidebar(QWidget):
    def __init__(self, catalog: Dict[str, CatalogItem]):
        super().__init__()
        self.catalog = catalog
        self._visible_ids: List[str] = []
        self._cached_labels: Set[str] = set()  # Cache for selected labels
        self._labels_dirty: bool = True  # Flag to invalidate cache

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.setFixedWidth(360)
        self._reposition_right()

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title = QLabel("Blackbox Settings")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: white;")
        layout.addWidget(title)

        self.enable_overlay = QCheckBox("Enable boxes overlay")
        self.enable_overlay.setChecked(True)
        self.enable_overlay.setStyleSheet("color: white;")
        layout.addWidget(self.enable_overlay)

        layout.addWidget(QLabel("Match threshold"))
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(60)
        self.threshold_slider.setMaximum(95)
        self.threshold_slider.setValue(86)
        layout.addWidget(self.threshold_slider)

        # ---- Search + selectable items ----
        layout.addWidget(QLabel("Find items to detect"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search items…")
        self.search.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search)

        self.list = QListWidget()
        self.list.setAlternatingRowColors(True)
        self.list.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.list, stretch=1)

        btn_row = QVBoxLayout()

        # self.btn_select_all = QPushButton("Select all (filtered)")
        # self.btn_select_all.clicked.connect(self._select_all_filtered)
        # btn_row.addWidget(self.btn_select_all)

        self.btn_clear = QPushButton("Clear selection")
        self.btn_clear.clicked.connect(self._clear_selection)
        btn_row.addWidget(self.btn_clear)

        close_btn = QPushButton("Close (Alt+Hotkey)")
        close_btn.clicked.connect(self.hide)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

        self.setLayout(layout)

        self.setStyleSheet("""
            QWidget {
                background-color: rgba(88, 88, 88, 210);
                border: 1px solid rgba(255,255,255,60);
                border-radius: 12px;
            }
            QLabel { color: white; }
            QLineEdit {
                padding: 8px;
                border-radius: 10px;
                background-color: rgba(255,255,255,18);
                color: white;
                border: 1px solid rgba(255,255,255,40);
            }
            QListWidget {
                background-color: rgba(255,255,255,10);
                color: white;
                border: 1px solid rgba(255,255,255,30);
                border-radius: 10px;
            }
            QPushButton {
                padding: 8px;
                border-radius: 10px;
                background-color: rgba(255,255,255,30);
                color: white;
            }
            QPushButton:hover { background-color: rgba(255,255,255,45); }
        """)

        self._populate_list()
        self.hide()

    def _reposition_right(self):
        geo = self.screen().availableGeometry()
        x = geo.x() + geo.width() - self.width() - 20
        y = geo.y() + 100
        self.move(x, y)

    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self._reposition_right()
            self.show()
            self.raise_()
            self.activateWindow()
            self.search.setFocus()

    # -------- list/search logic --------

    def _populate_list(self):
        self.list.blockSignals(True)
        self.list.clear()

        # default visible: all
        self._visible_ids = list(self.catalog.keys())

        for item_id, item in self.catalog.items():
            witem = QListWidgetItem(item.name)
            witem.setFlags(witem.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            witem.setCheckState(Qt.CheckState.Unchecked)
            witem.setData(Qt.ItemDataRole.UserRole, item_id)
            self.list.addItem(witem)

        self.list.blockSignals(False)

    def _apply_filter(self, text: str):
        q = text.strip().lower()
        self._visible_ids = []

        for i in range(self.list.count()):
            witem = self.list.item(i)
            item_id = witem.data(Qt.ItemDataRole.UserRole)
            item = self.catalog[item_id]
            visible = (q in item.name.lower()) or (q in item_id.lower()) or (q == "")
            witem.setHidden(not visible)
            if visible:
                self._visible_ids.append(item_id)

    def _select_all_filtered(self):
        self.list.blockSignals(True)
        for i in range(self.list.count()):
            witem = self.list.item(i)
            if not witem.isHidden():
                witem.setCheckState(Qt.CheckState.Checked)
        self.list.blockSignals(False)

    def _clear_selection(self):
        self.list.blockSignals(True)
        for i in range(self.list.count()):
            self.list.item(i).setCheckState(Qt.CheckState.Unchecked)
        self.list.blockSignals(False)
        self._labels_dirty = True  # Invalidate cache

    def _on_item_changed(self, _):
        self._labels_dirty = True  # Invalidate cache when selection changes

    def selected_item_ids(self) -> Set[str]:
        out: Set[str] = set()
        for i in range(self.list.count()):
            witem = self.list.item(i)
            if witem.checkState() == Qt.CheckState.Checked:
                out.add(witem.data(Qt.ItemDataRole.UserRole))
        return out

    def selected_template_labels(self) -> Set[str]:
        """Return cached selected labels, only recompute when dirty."""
        if self._labels_dirty:
            labels: Set[str] = set()
            for i in range(self.list.count()):
                witem = self.list.item(i)
                if witem.checkState() == Qt.CheckState.Checked:
                    item_id = witem.data(Qt.ItemDataRole.UserRole)
                    for lab in self.catalog[item_id].template_labels:
                        labels.add(lab.upper())
            self._cached_labels = labels
            self._labels_dirty = False
        return self._cached_labels
