"""Display-free tests for the capture math + naming (v1 phase-1 port)."""
import datetime

from gi.repository import GdkPixbuf

from linscreencapture2.core import capture
from linscreencapture2.core.capture import Rect


def _pix(w: int, h: int, pixel: int = 0xFF000000) -> GdkPixbuf.Pixbuf:
    # fill() maps the guint32 as 0xRRGGBB00 for no-alpha pixbufs
    pb = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, w, h)
    pb.fill(pixel)
    return pb


def test_rect_normalized_negative_drag():
    r = Rect(100, 80, -40, -20).normalized
    assert (r.x, r.y, r.w, r.h) == (60, 60, 40, 20)


def test_rect_clamp_partial_offscreen():
    assert Rect(-5, -2, 10, 8).clamped_to(100, 100) == Rect(0, 0, 5, 6)
    assert Rect(90, 95, 20, 20).clamped_to(100, 100) == Rect(90, 95, 10, 5)
    assert Rect(99, 99, 50, 50).clamped_to(100, 100) == Rect(99, 99, 1, 1)


def test_rect_too_small_matches_v1():
    assert Rect(0, 0, 4, 100).too_small
    assert Rect(0, 0, 100, 4).too_small
    assert not Rect(0, 0, 5, 5).too_small


def test_crop_synthetic():
    out = capture.crop(_pix(10, 8), Rect(2, 3, 4, 5))
    assert (out.get_width(), out.get_height()) == (4, 5)
    px = out.get_pixels()
    assert px[0] == 0xFF and px[1] == 0x00 and px[2] == 0x00  # fill survived the crop


def test_crop_empty_when_outside():
    assert capture.crop(_pix(10, 8), Rect(20, 20, 5, 5)) is None


def test_filename_stamp_uses_v1_pattern():
    when = datetime.datetime(2026, 10, 7, 1, 48, 9)
    assert capture.filename_stamp(when) == "LinCapture_20261007_014809.png"


def test_save_png_never_overwrites(tmp_path):
    when = datetime.datetime(2026, 10, 7, 12, 0, 0)
    p1 = capture.save_png(_pix(4, 4), tmp_path, when)
    p2 = capture.save_png(_pix(4, 4), tmp_path, when)
    assert p1.name == "LinCapture_20261007_120000.png"
    assert p2.name != p1.name and p1.exists() and p2.exists()
