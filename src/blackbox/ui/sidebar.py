from __future__ import annotations

import json
from typing import Dict, List, Set

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSlider, QCheckBox, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QApplication
)

from blackbox.catalog import CatalogItem
from blackbox.utils.paths import ensure_data_dir


SELECTION_FILE = "selected_items.json"


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
        self.list.itemClicked.connect(self._on_item_clicked)  # Click anywhere on row to toggle
        layout.addWidget(self.list, stretch=1)

        btn_row = QVBoxLayout()
        btn_row.setSpacing(6)

        self.btn_show_selected = QPushButton("Show selected only")
        self.btn_show_selected.clicked.connect(self._filter_selected_only)
        btn_row.addWidget(self.btn_show_selected)
        
        self.btn_show_all = QPushButton("Show all items")
        self.btn_show_all.clicked.connect(self._show_all_items)
        btn_row.addWidget(self.btn_show_all)

        self.btn_clear = QPushButton("Deselect all")
        self.btn_clear.clicked.connect(self._clear_selection)
        btn_row.addWidget(self.btn_clear)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.hide)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

        self.setLayout(layout)

        self.setStyleSheet("""
            QWidget {
                background-color: rgb(30, 30, 35);
                border: 1px solid rgb(60, 60, 65);
                border-radius: 12px;
            }
            QLabel { 
                color: white; 
                background-color: transparent;
                border: none;
            }
            QLineEdit {
                padding: 8px;
                border-radius: 10px;
                background-color: rgb(45, 45, 50);
                color: white;
                border: 1px solid rgb(70, 70, 75);
            }
            QListWidget {
                background-color: rgb(40, 40, 45);
                color: white;
                border: 1px solid rgb(60, 60, 65);
                border-radius: 10px;
            }
            QListWidget::item {
                padding: 4px;
            }
            QListWidget::item:selected {
                background-color: rgb(60, 60, 70);
            }
            QListWidget::item:hover {
                background-color: rgb(50, 50, 58);
            }
            QCheckBox {
                color: white;
                background-color: transparent;
                border: none;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QSlider::groove:horizontal {
                background: rgb(50, 50, 55);
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: rgb(100, 180, 100);
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QPushButton {
                padding: 8px;
                border-radius: 10px;
                background-color: rgb(55, 55, 60);
                color: white;
                border: 1px solid rgb(70, 70, 75);
            }
            QPushButton:hover { 
                background-color: rgb(70, 70, 80); 
            }
            QPushButton:pressed { 
                background-color: rgb(50, 50, 55); 
            }
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

    # -------- Persistence --------
    
    def _get_selection_path(self):
        return ensure_data_dir() / SELECTION_FILE
    
    def _load_selection(self) -> Set[str]:
        """Load saved selection from disk."""
        path = self._get_selection_path()
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return set(data.get("selected_ids", []))
            except (json.JSONDecodeError, IOError):
                pass
        return set()
    
    def _save_selection(self):
        """Save current selection to disk."""
        path = self._get_selection_path()
        selected = list(self.selected_item_ids())
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"selected_ids": selected}, f, indent=2)
        except IOError as e:
            print(f"Failed to save selection: {e}")

    # -------- list/search logic --------

    def _populate_list(self):
        self.list.blockSignals(True)
        self.list.clear()

        # Load previously saved selection
        saved_selection = self._load_selection()

        # default visible: all
        self._visible_ids = list(self.catalog.keys())

        for item_id, item in self.catalog.items():
            witem = QListWidgetItem(item.name)
            witem.setFlags(witem.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            # Restore saved selection state
            if item_id in saved_selection:
                witem.setCheckState(Qt.CheckState.Checked)
            else:
                witem.setCheckState(Qt.CheckState.Unchecked)
            witem.setData(Qt.ItemDataRole.UserRole, item_id)
            self.list.addItem(witem)

        self.list.blockSignals(False)
        self._labels_dirty = True  # Recalculate labels after loading

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
        self._labels_dirty = True
        self._save_selection()  # Persist to disk

    def _clear_selection(self):
        self.list.blockSignals(True)
        for i in range(self.list.count()):
            self.list.item(i).setCheckState(Qt.CheckState.Unchecked)
        self.list.blockSignals(False)
        self._labels_dirty = True  # Invalidate cache
        self._save_selection()  # Persist to disk

    def _filter_selected_only(self):
        """Show only items that are currently selected."""
        self.search.clear()  # Clear any existing search
        for i in range(self.list.count()):
            witem = self.list.item(i)
            is_checked = witem.checkState() == Qt.CheckState.Checked
            witem.setHidden(not is_checked)
    
    def _show_all_items(self):
        """Show all items (reset filter)."""
        self.search.clear()
        for i in range(self.list.count()):
            self.list.item(i).setHidden(False)

    def _on_item_changed(self, _):
        self._labels_dirty = True  # Invalidate cache when selection changes
        self._save_selection()  # Persist to disk

    def _on_item_clicked(self, item: QListWidgetItem):
        """Toggle checkbox when clicking anywhere on the row."""
        if item.checkState() == Qt.CheckState.Checked:
            item.setCheckState(Qt.CheckState.Unchecked)
        else:
            item.setCheckState(Qt.CheckState.Checked)

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
