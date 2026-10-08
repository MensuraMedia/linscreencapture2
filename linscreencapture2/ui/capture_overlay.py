"""Freeze-frame selection overlay - GTK4 port of v1 capture_overlay.c.

Phase-1 semantics: the caller grabs the whole-root frozen frame BEFORE
constructing this overlay (freeze-frame invariant), then run() shows one
undecorated fullscreen window per monitor over that frozen frame.

- drag >= 5px  -> live region selection (dim outside, dashed border, size chip)
- drag < 5px / click  -> cancel (v1 phase-1 click had nothing to snap to)
- Esc -> cancel, Return -> accept the current selection
- red crosshair follows the pointer; selections can span monitors

Window snapping (v1 phase-3 geometry hit-test) is a separate port.
"""

from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from linscreencapture2.core.capture import Rect  # noqa: E402

DRAG_THRESHOLD = 4  # v1: held press becomes a selection after ~4px


class FreezeOverlay:
    def __init__(self, frame):
        self.frame = frame
        self.selection: Rect | None = None  # raw rect while dragging (may be negative)
        self._selecting = False
        self._anchor = (0, 0)  # root coords of the press
        self._pointer = (-1, -1)  # root coords, for the crosshair
        self._mons: list[tuple[int, int, int, int]] = []  # (x, y, w, h) per window
        self._windows: list[Gtk.Window] = []
        self._areas: list[Gtk.DrawingArea] = []
        self._done = False
        self._on_done: Callable[[Rect | None], None] | None = None

    def run(self, on_done: Callable[[Rect | None], None]) -> None:
        """Show the frozen overlays; on_done(rect) fires once on finish/cancel."""
        self._on_done = on_done
        display = Gdk.Display.get_default()
        monitors = display.get_monitors()  # ListModel of Gdk.Monitor
        n = monitors.get_n_items()
        if n < 1:
            on_done(None)
            return
        for i in range(n):
            mon = monitors.get_item(i)
            geo = mon.get_geometry()
            self._mons.append((geo.x, geo.y, geo.width, geo.height))
            self._windows.append(self._build_window(display, mon, i))

        for win in self._windows:
            win.present()

        surface = self._windows[0].get_surface()
        if surface is not None:
            try:
                seat = display.get_default_seat()
                seat.grab(surface, Gdk.SeatCapability.ALL_POINTING, True,
                          None, None, None)
            except Exception:
                pass  # keyboard still reaches the focused overlay window

    def _build_window(self, display, mon, mon_idx: int) -> Gtk.Window:
        # GTK4 dropped the taskbar/keep-above WM hints; undecorated
        # fullscreen windows mapped last stack above everything else
        win = Gtk.Window()
        win.set_decorated(False)
        win.connect("close-request", lambda *_: self._finish(None))

        area = Gtk.DrawingArea()
        area.set_hexpand(True)
        area.set_vexpand(True)
        area.set_draw_func(self._draw, mon_idx)
        win.set_child(area)
        self._areas.append(area)

        drag = Gtk.GestureDrag()
        drag.connect("drag-begin", self._drag_begin, mon_idx)
        drag.connect("drag-update", self._drag_update, mon_idx)
        drag.connect("drag-end", self._drag_end, mon_idx)
        win.add_controller(drag)

        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self._motion, mon_idx)
        win.add_controller(motion)

        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._key_pressed)
        win.add_controller(keys)

        win.fullscreen_on_monitor(mon)
        return win

    # --- input ---------------------------------------------------------------

    def _to_root(self, x: float, y: float, mon_idx: int) -> tuple[int, int]:
        mx, my, _, _ = self._mons[mon_idx]
        return int(x) + mx, int(y) + my

    def _drag_begin(self, _g, x: float, y: float, mon_idx: int):
        rx, ry = self._to_root(x, y, mon_idx)
        self._anchor = (rx, ry)
        self._selecting = False
        self.selection = Rect(rx, ry, 0, 0)
        self._redraw()

    def _drag_update(self, _g, dx: float, dy: float, _mon_idx: int):
        ax, ay = self._anchor
        rx, ry = ax + int(dx), ay + int(dy)  # gesture reports start offsets
        if not self._selecting:
            ddx, ddy = rx - ax, ry - ay
            if ddx * ddx + ddy * ddy > DRAG_THRESHOLD * DRAG_THRESHOLD:
                self._selecting = True
        if self._selecting:
            self.selection = Rect(ax, ay, rx - ax, ry - ay)
        self._redraw()

    def _drag_end(self, _g, _dx: float, _dy: float, _mon_idx: int):
        if not self._selecting:
            self._finish(None)  # click without drag: nothing to snap to (yet)
            return
        rect = self.selection.normalized if self.selection else None
        if rect is None or rect.too_small:
            self._finish(None)
        else:
            self._finish(rect)

    def _motion(self, _c, x: float, y: float, mon_idx: int):
        self._pointer = self._to_root(x, y, mon_idx)
        self._redraw()

    def _key_pressed(self, _c, keyval, _kstate):
        if keyval == Gdk.KEY_Escape:
            self._finish(None)
            return True
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            rect = self.selection.normalized if self.selection else None
            self._finish(rect if rect and rect.w > 0 and rect.h > 0 else None)
            return True
        return False

    # --- drawing ---------------------------------------------------------------

    def _redraw(self):
        for area in self._areas:
            area.queue_draw()

    def _draw(self, _area, cr, _w, _h, mon_idx: int):
        mx, my, mw, mh = self._mons[mon_idx]
        cr.translate(-mx, -my)
        cr.rectangle(mx, my, mw, mh)
        cr.clip()

        if self.frame is not None:
            Gdk.cairo_set_source_pixbuf(cr, self.frame, 0, 0)
            cr.paint()

        cr.set_source_rgba(0.0, 0.0, 0.0, 0.5)
        sel = self.selection.normalized if self.selection else None
        if sel and self._selecting:
            x, y, w, h = sel.x, sel.y, sel.w, sel.h
            cr.rectangle(mx, my, mw, y - my)                 # above
            cr.rectangle(mx, y + h, mw, my + mh - (y + h))    # below
            cr.rectangle(mx, y, x - mx, h)                    # left
            cr.rectangle(x + w, y, mx + mw - (x + w), h)      # right
            cr.fill()

            cr.set_source_rgb(1.0, 1.0, 1.0)
            cr.set_line_width(1.0)
            cr.set_dash([4.0, 4.0])
            cr.rectangle(x, y, w, h)
            cr.stroke()
            cr.set_dash([])

            dims = f"{w}\u00d7{h}"
            ext = cr.text_extents(dims)
            text_x = x + w - ext.width - 10
            text_y = y - 10
            cr.set_source_rgba(0.0, 0.0, 0.0, 0.7)
            cr.rectangle(text_x - 5, text_y - ext.height - 5,
                         ext.width + 10, ext.height + 10)
            cr.fill()
            cr.set_source_rgb(1.0, 1.0, 1.0)
            cr.move_to(text_x, text_y)
            cr.show_text(dims)
        else:
            cr.paint()  # not selecting: dim the whole monitor (v1)

        px, py = self._pointer
        if mx <= px < mx + mw and my <= py < my + mh:
            cr.set_source_rgb(1.0, 0.0, 0.0)
            cr.set_line_width(2.0)
            cr.move_to(px - 12, py)
            cr.line_to(px + 12, py)
            cr.move_to(px, py - 12)
            cr.line_to(px, py + 12)
            cr.stroke()

    # --- teardown ---------------------------------------------------------------

    def _finish(self, rect: Rect | None):
        if self._done:
            return
        self._done = True
        try:
            seat = Gdk.Display.get_default().get_default_seat()
            if seat is not None:
                seat.ungrab()
        except Exception:
            pass
        for win in self._windows:
            win.destroy()
        self._windows.clear()
        self._areas.clear()
        if self._on_done is not None:
            self._on_done(rect)
