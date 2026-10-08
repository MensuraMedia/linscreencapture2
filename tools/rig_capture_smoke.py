"""Rig smoke: end-to-end freeze-frame capture inside Xephyr (r035).

Prerequisites (from the repo root):
    Xephyr :61 -screen 1280x800 &
    DISPLAY=:61 muffin --replace &      # or marco / openbox
    HOME=/tmp/lsc2-rig DISPLAY=:61 python3 tools/rig_capture_smoke.py

Drives the real UI path with XTEST pointer events: shell maps -> region
capture (frozen overlay + drag) -> Base layer on the canvas -> Save writes
the PNG into the sandbox HOME. Exits 0 and prints RIG PASS on success.
Rig renders land in /tmp/lsc2-rig/: overlay_mid_drag.png, canvas_after.png.
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("NO_AT_BRIDGE", "1")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RENDER_DIR = Path(os.environ.get("LSC2_RIG_DIR", "/tmp/lsc2-rig"))

import ctypes  # noqa: E402

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import GLib, Gtk  # noqa: E402

from linscreencapture2.app import App  # noqa: E402
from linscreencapture2.core import capture  # noqa: E402

# drag geometry as fractions of the root (muffin may resize the Xephyr
# root to a host RandR mode, so nothing can assume the -screen size)
DRAG_FRAC = (0.30, 0.30, 0.70, 0.70)  # x0 y0 x1 y1

xtst = ctypes.CDLL("libXtst.so.6")
x11 = ctypes.CDLL("libX11.so.6")
x11.XOpenDisplay.restype = ctypes.c_void_p
x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_bool]
_dpy = x11.XOpenDisplay(os.environ.get("DISPLAY", "").encode()) or None


def _motion(x: int, y: int):
    xtst.XTestFakeMotionEvent(_dpy, -1, x, y, 0)
    x11.XSync(_dpy, False)


def _button(down: bool):
    xtst.XTestFakeButtonEvent(_dpy, 1, down, 0)
    x11.XSync(_dpy, False)


class Driver:
    def __init__(self):
        self.app = App()
        self.win = None
        self.errors: list[str] = []
        self._pressed = False
        self._drag_step = 0

    def run(self):
        self.app.connect("activate", self._on_activate)
        GLib.timeout_add(20000, self._fail_timeout)
        self.app.run(None)
        if self.errors:
            print("FAIL:", "; ".join(self.errors))
            return 1
        print("RIG PASS: freeze-frame region capture end-to-end")
        return 0

    # --- steps ------------------------------------------------------------------

    def _on_activate(self, app):
        # the do_activate override runs after instance handlers, so the
        # studio window registers a tick later - pick it up on a timeout
        GLib.timeout_add(700, self._begin)
        return True

    def _begin(self):
        windows = self.app.get_windows()
        self.win = windows[0] if windows else None
        if self.win is None:
            self.errors.append("studio window did not register with the app")
            self.app.quit()
            return False

        mon = self.app.get_windows()[0].get_display().get_monitors().get_item(0)
        geo = mon.get_geometry()
        fx0, fy0, fx1, fy1 = DRAG_FRAC
        self.drag = (
            int(geo.width * fx0), int(geo.height * fy0),
            int(geo.width * fx1), int(geo.height * fy1),
        )
        self.exp_wh = (self.drag[2] - self.drag[0], self.drag[3] - self.drag[1])
        print(f"rig: root monitor {geo.width}x{geo.height}, "
              f"drag {self.drag} -> {self.exp_wh[0]}x{self.exp_wh[1]}")

        # gradient helper window: gives the frozen frame non-uniform pixels
        helper = Gtk.Window()
        helper.set_decorated(False)
        helper.fullscreen()
        da = Gtk.DrawingArea()
        da.set_draw_func(self._draw_gradient)
        helper.set_child(da)
        helper.connect("close-request", lambda *_: True)
        helper.present()
        self.helper = helper

        GLib.timeout_add(700, self._start_capture)
        return False

    @staticmethod
    def _draw_gradient(_a, cr, w, h):
        # top red -> bottom blue, full width
        top, bottom = (1.0, 0.35, 0.2), (0.2, 0.35, 1.0)
        for y in range(h):
            t = y / max(h - 1, 1)
            cr.set_source_rgb(
                top[0] + (bottom[0] - top[0]) * t,
                top[1] + (bottom[1] - top[1]) * t,
                top[2] + (bottom[2] - top[2]) * t,
            )
            cr.rectangle(0, y, w, 1)
            cr.fill()

    def _start_capture(self):
        print("step: start region capture")
        self.win._start_capture("region")
        GLib.timeout_add(600, self._drag_tick)
        return False

    def _drag_tick(self):
        x0, y0, x1, y1 = self.drag
        steps = [
            (x0, y0, False),
            (x0, y0, True),
            (x0 + (x1 - x0) // 5, y0 + (y1 - y0) // 8, True),
            (x0 + (x1 - x0) // 3, y0 + (y1 - y0) // 4, True),
            (x0 + (x1 - x0) * 13 // 30, y0 + (y1 - y0) * 17 // 60, True),
            (x1, y1, True),
            (x1, y1, False),
        ]
        if self._drag_step < len(steps):
            x, y, pressed = steps[self._drag_step]
            _motion(x, y)
            if pressed != self._pressed:
                _button(pressed)
                self._pressed = pressed
            if self._drag_step == 3:
                self._shot("overlay_mid_drag.png")
            self._drag_step += 1
            return True
        GLib.timeout_add(500, self._check_result)
        return False

    def _shot(self, name: str):
        pb = capture.grab_root()
        if pb is not None:
            RENDER_DIR.mkdir(parents=True, exist_ok=True)
            pb.savev(str(RENDER_DIR / name), "png", [], [])
            print(f"shot: {RENDER_DIR / name}")

    def _check_result(self):
        pix = self.win._capture
        if pix is None:
            self.errors.append("no Base layer on canvas after drag release")
        else:
            w, h = pix.get_width(), pix.get_height()
            exp_w, exp_h = self.exp_wh
            print(f"step: canvas base layer {w}x{h}")
            if (w, h) != (exp_w, exp_h):
                self.errors.append(f"crop size {w}x{h}, expected {exp_w}x{exp_h}")
            # gradient sanity: top row redder, bottom row bluer
            px = pix.get_pixels()
            row = pix.get_rowstride()  # crops keep the parent's stride
            top_r, top_b = px[0], px[2]
            bot_r, bot_b = px[row * (h - 1)], px[row * (h - 1) + 2]
            if not (top_r > top_b and bot_b > bot_r):
                self.errors.append(
                    f"gradient lost in crop: top(r,b)=({top_r},{top_b}) "
                    f"bottom(r,b)=({bot_r},{bot_b})")
            self._shot("canvas_after.png")
        GLib.timeout_add(300, self._do_save)
        return False

    def _do_save(self):
        print("step: save")
        self.win._save()
        path = self.win._saved_path
        if path is None or not path.exists() or path.stat().st_size == 0:
            self.errors.append(f"save failed ({path})")
        else:
            print(f"step: saved {path} ({path.stat().st_size} bytes)")
        self.helper.destroy()
        self.app.quit()
        return False

    def _fail_timeout(self):
        self.errors.append("timeout before completing all steps")
        self.app.quit()
        return False


if __name__ == "__main__":
    if _dpy is None:
        print("FAIL: cannot open DISPLAY for XTEST")
        sys.exit(2)
    sys.exit(Driver().run())
