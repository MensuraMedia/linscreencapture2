"""Capture pipeline core - port of v1 screen_capture.c (GTK3/C) to GTK4.

GTK4 removed Gdk.pixbuf_get_from_window and Gdk.Screen, so pixels come via
ctypes libX11 exactly as v1 phase 1 did: XOpenDisplay -> XGetImage on the
root window (AllPlanes, ZPixmap) -> GdkPixbuf. The freeze-frame invariant
carries over: grab_root() must be called before any overlay window exists.

Selection/crop math (Rect) is pure and display-free; unit tests cover it.
"""

import ctypes
import datetime
from dataclasses import dataclass
from pathlib import Path

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf  # noqa: E402

MIN_SELECTION = 5  # v1: selections under 5px in either axis are cancels


@dataclass(frozen=True)
class Rect:
    """A selection in root coordinates. w/h may be negative while dragging."""

    x: int
    y: int
    w: int
    h: int

    @property
    def normalized(self) -> "Rect":
        """Positive w/h with the origin moved to the top-left corner (v1)."""
        x, y, w, h = self.x, self.y, self.w, self.h
        if w < 0:
            x += w
            w = -w
        if h < 0:
            y += h
            h = -h
        return Rect(x, y, w, h)

    def clamped_to(self, frame_w: int, frame_h: int) -> "Rect":
        """Crop clamp from v1 capture_crop_surface: keep the intersection."""
        x, y, w, h = self.x, self.y, self.w, self.h
        if x < 0:
            w += x
            x = 0
        if y < 0:
            h += y
            y = 0
        w = min(w, frame_w - x)
        h = min(h, frame_h - y)
        return Rect(x, y, max(w, 0), max(h, 0))

    @property
    def too_small(self) -> bool:
        return self.w < MIN_SELECTION or self.h < MIN_SELECTION


# --- X11 grab (ctypes port of v1 capture_screen) ------------------------------

_libx11 = None


class _XImage(ctypes.Structure):
    # Fields past blue_mask are never read; left out.
    _fields_ = [
        ("width", ctypes.c_int),
        ("height", ctypes.c_int),
        ("xoffset", ctypes.c_int),
        ("format", ctypes.c_int),
        ("data", ctypes.POINTER(ctypes.c_ubyte)),
        ("byte_order", ctypes.c_int),  # 0 = LSBFirst
        ("bitmap_unit", ctypes.c_int),
        ("bitmap_bit_order", ctypes.c_int),
        ("bitmap_pad", ctypes.c_int),
        ("depth", ctypes.c_int),
        ("bytes_per_line", ctypes.c_int),
        ("bits_per_pixel", ctypes.c_int),
        ("red_mask", ctypes.c_ulong),
        ("green_mask", ctypes.c_ulong),
        ("blue_mask", ctypes.c_ulong),
    ]


class _XWindowAttributes(ctypes.Structure):
    # Only width/height are read; the rest pins the C layout.
    _fields_ = [
        ("x", ctypes.c_int), ("y", ctypes.c_int),
        ("width", ctypes.c_int), ("height", ctypes.c_int),
        ("border_width", ctypes.c_int), ("depth", ctypes.c_int),
        ("visual", ctypes.c_void_p), ("root", ctypes.c_ulong),
        ("c_class", ctypes.c_int), ("bit_gravity", ctypes.c_int),
        ("win_gravity", ctypes.c_int), ("backing_store", ctypes.c_int),
        ("backing_planes", ctypes.c_ulong), ("backing_pixel", ctypes.c_ulong),
        ("save_under", ctypes.c_int), ("colormap", ctypes.c_ulong),
        ("map_installed", ctypes.c_int), ("map_state", ctypes.c_int),
        ("all_event_masks", ctypes.c_long), ("your_event_mask", ctypes.c_long),
        ("do_not_propagate_mask", ctypes.c_long),
        ("override_redirect", ctypes.c_int), ("screen", ctypes.c_void_p),
    ]


def _x11() -> ctypes.CDLL:
    global _libx11
    if _libx11 is None:
        _libx11 = ctypes.CDLL("libX11.so.6")
        _libx11.XOpenDisplay.restype = ctypes.c_void_p
        _libx11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        _libx11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        _libx11.XAllPlanes.restype = ctypes.c_ulong
        _libx11.XGetImage.restype = ctypes.POINTER(_XImage)
        _libx11.XGetImage.argtypes = [
            ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_int,
            ctypes.c_uint, ctypes.c_uint, ctypes.c_ulong, ctypes.c_int,  # ZPixmap=2
        ]
        _libx11.XDestroyImage.argtypes = [ctypes.POINTER(_XImage)]
        _libx11.XDefaultRootWindow.restype = ctypes.c_ulong
        _libx11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
        _libx11.XGetWindowAttributes.restype = ctypes.c_int
        _libx11.XGetWindowAttributes.argtypes = [
            ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(_XWindowAttributes)
        ]
    return _libx11


def display_is_x11() -> bool:
    display = Gdk.Display.get_default()
    if display is None:
        return False
    return display.__class__.__name__.startswith("X11")


def grab_root() -> GdkPixbuf.Pixbuf | None:
    """Snapshot the whole root window. Must run before any overlay exists."""
    x11 = _x11()
    dpy = x11.XOpenDisplay(None)
    if not dpy:
        return None
    try:
        root = x11.XDefaultRootWindow(dpy)
        if not root:
            return None
        wattr = _XWindowAttributes()
        if not x11.XGetWindowAttributes(dpy, root, ctypes.byref(wattr)):
            return None
        # XGetImage errors on rects outside the drawable, so pass exact dims.
        img = x11.XGetImage(dpy, root, 0, 0, wattr.width, wattr.height,
                            x11.XAllPlanes(), 2)
        if not img:
            return None
        try:
            return _pixbuf_from_ximage(img.contents)
        finally:
            x11.XDestroyImage(img)
    finally:
        x11.XCloseDisplay(dpy)


def _pixbuf_from_ximage(img: _XImage) -> GdkPixbuf.Pixbuf | None:
    w, h = img.width, img.height
    stride = img.bytes_per_line
    if w <= 0 or h <= 0 or img.bits_per_pixel != 32:
        return None
    size = stride * h
    raw = bytes(ctypes.cast(img.data, ctypes.POINTER(ctypes.c_ubyte * size)).contents)
    rgb = bytes(_rgb_from_bgrx_rows(raw, w, h, stride)) \
        if (img.byte_order == 0 and img.red_mask == 0xFF0000
            and img.green_mask == 0xFF00 and img.blue_mask == 0xFF) \
        else bytes(_rgb_generic(raw, w, h, stride, img))
    # bytes() copy: new_from_data keeps the buffer alive for the pixbuf
    return GdkPixbuf.Pixbuf.new_from_data(
        rgb, GdkPixbuf.Colorspace.RGB, False, 8, w, h, w * 3
    )


def _rgb_from_bgrx_rows(raw: bytes, w: int, h: int, stride: int) -> bytearray:
    """LSBFirst BGRX rows -> RGB triples via C-speed slice assignments."""
    if stride == w * 4:
        buf = bytearray(raw)
        rgb = bytearray(w * h * 3)
        rgb[0::3] = buf[2::4]  # R
        rgb[1::3] = buf[1::4]  # G
        rgb[2::3] = buf[0::4]  # B
        return rgb
    out = bytearray(w * h * 3)
    for y in range(h):
        row = raw[y * stride:(y + 1) * stride]
        o = y * w * 3
        out[o:o + w * 3:3] = row[2::4][:w]
        out[o + 1:o + w * 3:3] = row[1::4][:w]
        out[o + 2:o + w * 3:3] = row[0::4][:w]
    return out


def _rgb_generic(raw: bytes, w: int, h: int, stride: int, img: _XImage) -> bytearray:
    """Any mask layout: per-pixel mask/shift math (v1 loop), numpy if present."""
    try:
        import numpy as np

        def shift(mask: int) -> int:
            s = 0
            while mask and not mask & 1:
                mask >>= 1
                s += 1
            return s

        rs, gs, bs = shift(img.red_mask), shift(img.green_mask), shift(img.blue_mask)
        rows = np.frombuffer(raw, dtype=np.uint8, count=stride * h).reshape(h, stride)
        px = rows[:, : w * 4].copy().view("<u4").reshape(h, w)
        rgb = np.empty((h, w, 3), dtype=np.uint8)
        rgb[:, :, 0] = ((px & img.red_mask) >> rs).astype(np.uint8)
        rgb[:, :, 1] = ((px & img.green_mask) >> gs).astype(np.uint8)
        rgb[:, :, 2] = ((px & img.blue_mask) >> bs).astype(np.uint8)
        return bytearray(rgb.tobytes())
    except ImportError:
        out = bytearray(w * h * 3)
        rm, gm, bm = img.red_mask, img.green_mask, img.blue_mask

        def sh(mask: int) -> int:
            s = 0
            while mask and not mask & 1:
                mask >>= 1
                s += 1
            return s

        rs, gs, bs = sh(rm), sh(gm), sh(bm)
        o = 0
        for y in range(h):
            for x in range(w):
                p = int.from_bytes(raw[y * stride + x * 4: y * stride + x * 4 + 4], "little")
                out[o] = (p & rm) >> rs
                out[o + 1] = (p & gm) >> gs
                out[o + 2] = (p & bm) >> bs
                o += 3
        return out


# --- crop / save ---------------------------------------------------------------

def crop(frame: GdkPixbuf.Pixbuf, rect: Rect) -> GdkPixbuf.Pixbuf | None:
    """Clamped sub-copy of the frozen frame (v1 capture_crop_surface)."""
    r = rect.normalized.clamped_to(frame.get_width(), frame.get_height())
    if r.w <= 0 or r.h <= 0:
        return None
    return frame.new_subpixbuf(r.x, r.y, r.w, r.h).copy()


def filename_stamp(when: datetime.datetime | None = None) -> str:
    """v1 naming: LinCapture_YYYYmmdd_HHMMSS.png."""
    return f"LinCapture_{(when or datetime.datetime.now()):%Y%m%d_%H%M%S}.png"


def unique_path(folder: Path, name: str) -> Path:
    path = folder / name
    n = 2
    stem, dot, ext = name.rpartition(".")
    while path.exists():
        path = folder / f"{stem}-{n}.{ext}" if dot else folder / f"{name}-{n}"
        n += 1
    return path


def save_png(pixbuf: GdkPixbuf.Pixbuf, folder: Path, when: datetime.datetime | None = None) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = unique_path(folder, filename_stamp(when))
    pixbuf.savev(str(path), "png", [], [])
    return path
