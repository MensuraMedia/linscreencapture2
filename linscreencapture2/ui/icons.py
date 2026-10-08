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
    """The icon `name` at `size` px in `color` (default: theme text colour).

    The glyph's INK is normalized to fill the square uniformly (r057):
    rendered oversized, cropped to its drawn bounds, then scaled so every
    icon's mark measures the same dimensions regardless of how much of
    the source viewBox the artwork occupies."""
    path = os.path.join(ICON_DIR, f"{name}.svg")
    with open(path, encoding="utf-8") as f:
        svg = f.read().replace("currentColor", color or tokens.COLOR["text"])
    loader = GdkPixbuf.PixbufLoader.new_with_type("svg")
    loader.set_size(size * 4, size * 4)  # oversample for clean scaling
    loader.write(svg.encode())
    loader.close()
    src = loader.get_pixbuf()
    return _ink_normalized(src, size)


def _ink_bounds(src: GdkPixbuf.Pixbuf):
    """Bounding box of visible (alpha > 8) pixels, or None if empty."""
    px, W, H, rs = src.get_pixels(), src.get_width(), src.get_height(), src.get_rowstride()
    x0, y0, x1, y1 = W, H, -1, -1
    for y in range(H):
        row = y * rs
        for x in range(W):
            if px[row + x * 4 + 3] > 8:
                if x < x0: x0 = x
                if x > x1: x1 = x
                if y < y0: y0 = y
                if y > y1: y1 = y
    if x1 < 0:
        return None
    return (x0, y0, x1 - x0 + 1, y1 - y0 + 1)


def _ink_normalized(src: GdkPixbuf.Pixbuf, size: int) -> GdkPixbuf.Pixbuf:
    bounds = _ink_bounds(src)
    if bounds is None:
        return src.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
    bx, by, bw, bh = bounds
    glyph = src.new_subpixbuf(bx, by, bw, bh)
    # uniform fit: the long edge becomes exactly `size`
    scale = size / max(bw, bh)
    dw, dh = max(1, round(bw * scale)), max(1, round(bh * scale))
    scaled = glyph.scale_simple(dw, dh, GdkPixbuf.InterpType.BILINEAR)
    out = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, size, size)
    out.fill(0x00000000)
    scaled.copy_area(0, 0, dw, dh, out, (size - dw) // 2, (size - dh) // 2)
    return out
