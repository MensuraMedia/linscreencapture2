"""Library access. v2 opens the v1 catalog in place when present
(D2): same captures folder, same library.db, same layers."""

import sqlite3
from pathlib import Path

from linscreencapture2.core import paths


def open_library() -> sqlite3.Connection | None:
    """Read-only handle on the v1 catalog, if it exists."""
    db = paths.v1_library_db()
    if not db:
        return None
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def recent_captures(limit: int = 50) -> list[Path]:
    root = paths.v1_screenshot_path()
    if not root:
        return []
    exts = {".png", ".jpg", ".jpeg"}
    files = [p for p in sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
             if p.suffix.lower() in exts and not p.name.startswith(".")]
    return files[:limit]
