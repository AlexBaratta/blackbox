from __future__ import annotations

import os
import sys
import platform
from pathlib import Path


def project_root() -> Path:
    """
    Returns the correct root directory in both:
    - development (source checkout)
    - PyInstaller (onefile / onedir)
    """
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller extraction dir
        return Path(sys._MEIPASS)
    else:
        # src/blackbox/utils/paths.py -> parents[3] = project root
        return Path(__file__).resolve().parents[3]


def templates_dir() -> Path:
    return project_root() / "assets" / "templates"


def data_dir() -> Path:
    """
    Returns directory for persistent user data (settings, selections, etc.).
    
    Locations:
    - Windows: %APPDATA%/Blackbox (e.g., C:/Users/<user>/AppData/Roaming/Blackbox)
    - macOS: ~/Library/Application Support/Blackbox
    - Linux: ~/.local/share/Blackbox
    - Development: <project_root>/data
    """
    if hasattr(sys, "_MEIPASS"):
        # Running as packaged exe/app
        system = platform.system()
        
        if system == "Windows":
            base = Path(os.environ.get("APPDATA", Path.home()))
        elif system == "Darwin":  # macOS
            base = Path.home() / "Library" / "Application Support"
        else:  # Linux and others
            base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        
        return base / "Blackbox"
    else:
        # Development: use project root
        return project_root() / "data"


def ensure_data_dir() -> Path:
    """Ensure data directory exists and return it."""
    d = data_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d
