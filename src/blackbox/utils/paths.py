from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    # This file lives at src/blackbox/utils/paths.py
    # Parents: utils -> blackbox -> src -> PROJECT_ROOT
    return Path(__file__).resolve().parents[3]


def templates_dir() -> Path:
    return project_root() / "assets" / "templates"
