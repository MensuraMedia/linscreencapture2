"""Settings: v2 file with v1 import on first run (D2 - import v1 data)."""

import configparser
import dataclasses
from pathlib import Path

from linscreencapture2.core import paths


@dataclasses.dataclass
class Settings:
    screenshot_path: str = ""
    capture_delay: int = 0
    capture_mode: int = 0  # 0 region, 1 window, 2 monitor, 3 full

    @classmethod
    def load(cls) -> "Settings":
        s = cls()
        s.screenshot_path = str(paths.v1_screenshot_path() or (Path.home() / "Pictures" / "screenshots"))
        f = paths.V2_CONFIG_DIR / "settings.conf"
        if f.exists():
            cp = configparser.ConfigParser()
            cp.read(f)
            g = cp["Settings"] if cp.has_section("Settings") else {}
            s.screenshot_path = g.get("screenshot_path", s.screenshot_path)
            s.capture_delay = int(g.get("capture_delay", s.capture_delay))
            s.capture_mode = int(g.get("capture_mode", s.capture_mode))
        return s

    def save(self) -> None:
        paths.ensure_dirs()
        cp = configparser.ConfigParser()
        cp["Settings"] = {
            "screenshot_path": self.screenshot_path,
            "capture_delay": str(self.capture_delay),
            "capture_mode": str(self.capture_mode),
        }
        with open(paths.V2_CONFIG_DIR / "settings.conf", "w") as fh:
            cp.write(fh)
