"""Data locations. v1 (linshot3, GTK3/C) data is imported in place:
settings from ~/.config/linshot/settings.conf, captures + library.db from
the v1 screenshot path - the operator chose import-over-fresh (D2)."""

import os
from pathlib import Path

APP_NAME = "linscreencapture2"

V1_CONFIG = Path.home() / ".config" / "linshot" / "settings.conf"
V2_CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_NAME
V2_DATA_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / APP_NAME
V2_CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / APP_NAME


def v1_screenshot_path() -> Path | None:
    """The v1 captures folder (from v1 settings), if it exists."""
    if V1_CONFIG.exists():
        import configparser

        cp = configparser.ConfigParser()
        cp.read(V1_CONFIG)
        p = cp.get("Settings", "screenshot_path", fallback=None)
        if p and Path(p).is_dir():
            return Path(p)
    pics = Path.home() / "Pictures" / "screenshots"
    return pics if pics.is_dir() else None


def v1_library_db() -> Path | None:
    db = Path.home() / ".local" / "share" / "linscreencapture" / "library.db"
    return db if db.exists() else None


def ensure_dirs() -> None:
    for d in (V2_CONFIG_DIR, V2_DATA_DIR, V2_CACHE_DIR):
        d.mkdir(parents=True, exist_ok=True)
