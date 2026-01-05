from __future__ import annotations

import sys
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
