from __future__ import annotations

import ctypes
from ctypes import wintypes

from PyQt6.QtCore import QObject

user32 = ctypes.windll.user32

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
VK_B = 0x42


class HotkeyManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._callbacks: dict[int, callable] = {}

    def register_alt_b(self, hotkey_id: int, callback: callable) -> None:
        ok = user32.RegisterHotKey(None, hotkey_id, MOD_ALT, VK_B)
        if not ok:
            raise RuntimeError("RegisterHotKey failed (Alt+B). Another app may already be using it.")
        self._callbacks[hotkey_id] = callback

    def unregister_all(self) -> None:
        for hotkey_id in list(self._callbacks.keys()):
            user32.UnregisterHotKey(None, hotkey_id)
        self._callbacks.clear()

    def handle_native_event(self, event_type, message) -> bool:
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY:
            hotkey_id = int(msg.wParam)
            cb = self._callbacks.get(hotkey_id)
            if cb:
                cb()
                return True
        return False
