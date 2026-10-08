"""App-side icon loader over the full vendored Phosphor regular set.

The lintheme kit bundles a curated 20-icon subset in lintheme/icons/; this
project needs the whole palette, so the app loads straight from
assets/icons/phosphor/regular (same Phosphor v2 MIT source, same
currentColor mechanism) and the vendored kit stays stock.
"""

import functools
import os

import gi

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf  # noqa: E402

from lintheme import tokens  # noqa: E402

ICON_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "assets", "icons", "phosphor", "regular",
)


def names():
    """Bundled icon names"""
    return sorted(f[:-4] for f in os.listdir(ICON_DIR) if f.endswith(".svg"))


@functools.lru_cache(maxsize=512)
def pixbuf(name: str, size: int = 20, color: str | None = None) -> GdkPixbuf.Pixbuf:
    """The icon `name` at `size` px in `color` (default: theme text colour)."""
    path = os.path.join(ICON_DIR, f"{name}.svg")
    with open(path, encoding="utf-8") as f:
        svg = f.read().replace("currentColor", color or tokens.COLOR["text"])
    loader = GdkPixbuf.PixbufLoader.new_with_type("svg")
    loader.set_size(size, size)
    loader.write(svg.encode())
    loader.close()
    return loader.get_pixbuf()
