from __future__ import annotations

from typing import Callable, Dict, Optional

from pynput import keyboard


class HotkeyManager:
    """
    Cross-platform global hotkeys.

    Uses pynput.keyboard.GlobalHotKeys, which is much more reliable for modifier combos
    on Windows than manually feeding HotKey objects.
    """

    def __init__(self) -> None:
        self._mapping: Dict[str, Callable[[], None]] = {}
        self._listener: Optional[keyboard.GlobalHotKeys] = None

    def register_hotkey(self, hotkey_id: int, combo: str, callback: Callable[[], None]) -> None:
        # hotkey_id kept only for your API symmetry; combo is the actual key
        self._mapping[combo] = callback
        self._restart_listener()

    def unregister_all(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        self._mapping.clear()

    def _restart_listener(self) -> None:
        if self._listener is not None:
            self._listener.stop()

        self._listener = keyboard.GlobalHotKeys(self._mapping)
        self._listener.daemon = True
        self._listener.start()
