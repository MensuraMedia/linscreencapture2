"""StudioWindow - the Studio Editor shell (GTK4).

Regions per docs/design/STUDIO-EDITOR-SPEC.md section 3: header, options
bar, left rail (capture profiles + tools + color well), canvas, right
panel stack (Layers / Captures / Props), action bar. Theming via the
vendored lintheme kit (apply.install), GTK4.

r037 UI law: every button is an icon button - its label lives in the
tooltip, never on the surface. Spacing follows a 4px grid for evenness.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GLib, Gtk

from pathlib import Path

from lintheme import apply, tokens

from linscreencapture2.core import capture
from linscreencapture2.core.capture import Rect
from linscreencapture2.core.settings import Settings
from linscreencapture2.core import library
from linscreencapture2.ui import icons
from linscreencapture2.ui.capture_overlay import FreezeOverlay

# the studio window must be fully unmapped before the freeze-frame grab
HIDE_SETTLE_MS = 250

# the kit substitutes token values in Python (GTK 4.14 has no CSS var())
APP_CSS = f"""
.studio-header {{ border-bottom: 1px solid {tokens.COLOR['border']}; }}
.studio-options {{ border-bottom: 1px solid {tokens.COLOR['border']}; }}
.studio-rail {{ border-right: 1px solid {tokens.COLOR['border']}; }}
.studio-panels {{ border-left: 1px solid {tokens.COLOR['border']}; }}
.studio-actionbar {{ border-top: 1px solid {tokens.COLOR['border']}; }}

/* r034/r037 shape language: rounded squares only, labels live in tooltips */
.chip {{ border-radius: 6px; padding: 4px 10px; }}
.zoom {{ border-radius: 8px; background-color: {tokens.COLOR['surface']}; padding: 2px; }}
.sect {{ font-size: 11px; letter-spacing: 0.08em; }}

.icon-btn {{ padding: 0; border-radius: 6px; }}
.icon-32 {{ min-width: 32px; min-height: 32px; }}
.icon-24 {{ min-width: 24px; min-height: 24px; }}
.icon-24.primary {{
  background-color: {tokens.COLOR['accent']}; color: {tokens.COLOR['on_accent']};
}}
.icon-24.primary:hover {{ background-color: {tokens.COLOR['accent_hover']}; }}
.icon-danger {{ color: {tokens.COLOR['error']}; }}
""".encode()

PROFILE_ICONS = {
    "Region": "crop",
    "Window": "app-window",
    "Full screen": "monitor",
    "Scrolling": "arrows-out-line-vertical",
    "Delayed 3 s": "timer",
    "Pin to screen": "push-pin",
}

TOOL_ICONS = {
    "Select": "cursor", "Move": "arrows-out", "Line": "pen-nib",
    "Arrow": "arrow-up-right", "Box": "square", "Circle": "circle",
    "Text": "text-t", "Pen": "pen", "Marker": "marker-circle",
    "Blur": "circle-dashed", "Pixelate": "grid-four",
    "Step": "number-circle-one", "Callout": "chat-teardrop-text",
    "Fill": "paint-bucket", "Crop": "crop", "Resize": "arrows-horizontal",
    "Rotate": "arrow-clockwise", "Bright": "sun", "Dupe": "copy",
}

PANEL_ICONS = {"Layers": "stack", "Captures": "images", "Props": "sliders-horizontal"}


def _icon_button(name: str, tooltip: str, icon_px: int = 20,
                 css: tuple[str, ...] = ("icon-32",),
                 color: str | None = None) -> Gtk.Button:
    """Square icon button; the label is the tooltip (r037 law)."""
    pixbuf = icons.pixbuf(name, icon_px, color)
    b = Gtk.Button()
    b.set_child(Gtk.Image.new_from_paintable(Gdk.Texture.new_for_pixbuf(pixbuf)))
    b.set_tooltip_text(tooltip)
    ctx = b.get_style_context()
    ctx.add_class("lt-icon-btn")
    ctx.add_class("icon-btn")
    for c in css:
        ctx.add_class(c)
    return b


class StudioWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("LinScreenCapture")
        self.set_default_size(1280, 800)
        apply.install(self)
        self._install_css()
        self.get_style_context().add_class("studio-root")

        self.settings = Settings.load()
        self._frame = None  # whole-root frozen frame of the last capture
        self._capture = None  # cropped Base layer shown on the canvas
        self._saved_path: Path | None = None
        self._capturing = False
        self._build()

    def _install_css(self):
        # the kit loads its CSS at USER priority, so app CSS must load at
        # USER priority too (after apply.install) or kit rules win ties
        provider = Gtk.CssProvider()
        provider.load_from_data(APP_CSS)
        provider.connect("parsing-error", lambda _p, s, e: print(f"APP_CSS error: {e.message}"))
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

    def _build(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(root)

        root.append(self._build_header())
        middle = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        middle.set_vexpand(True)
        root.append(middle)
        middle.append(self._build_left_rail())
        middle.append(self._build_center())
        middle.append(self._build_right_panels())
        root.append(self._build_action_bar())

    def _build_header(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.get_style_context().add_class("studio-header")
        bar.get_style_context().add_class("lt-header")
        bar.set_margin_start(12); bar.set_margin_end(12)
        bar.set_margin_top(8); bar.set_margin_bottom(8)

        title = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        t = Gtk.Label(label="LinScreenCapture", halign=Gtk.Align.START)
        t.get_style_context().add_class("title")
        self._docsub = Gtk.Label(label="no capture yet", halign=Gtk.Align.START)
        self._docsub.get_style_context().add_class("muted")
        title.append(t); title.append(self._docsub)
        bar.append(title)

        chip = Gtk.Label(label="Ready")
        chip.get_style_context().add_class("chip")
        chip.set_margin_start(8)
        bar.append(chip)

        spacer = Gtk.Box(); bar.append(spacer); spacer.set_hexpand(True)

        zoom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        zoom.get_style_context().add_class("zoom")
        zoom.append(_icon_button("minus", "Zoom out (zoom model lands later)", 16))
        pct = Gtk.Label(label="100%")
        pct.set_margin_start(8); pct.set_margin_end(8)
        zoom.append(pct)
        zoom.append(_icon_button("plus", "Zoom in (zoom model lands later)", 16))
        zoom.append(_icon_button("arrows-in", "Fit to window (zoom model lands later)", 16))
        bar.append(zoom)

        cap = _icon_button(
            "camera", "Capture - freeze the screen and select a region (PrintScreen)",
            14, css=("icon-24", "primary"), color=tokens.COLOR["on_accent"],
        )
        cap.connect("clicked", lambda *_: self._start_capture("region"))
        bar.append(cap)
        return bar

    # --- capture pipeline (v1 freeze-frame port) --------------------------------

    def _start_capture(self, mode: str, delay_s: int | None = None):
        """mode: "region" (overlay select) or "fullscreen" (whole root)."""
        if self._capturing:
            return
        if not capture.display_is_x11():
            self.set_status("Capture needs X11 (Wayland portal is a later port)")
            return
        self._capturing = True
        self.settings.capture_mode = 0 if mode == "region" else 3
        self.settings.save()
        if delay_s is None:
            delay_s = self.settings.capture_delay
        # hide first so the studio window never lands in the frozen frame
        self.hide()
        GLib.timeout_add(max(HIDE_SETTLE_MS, delay_s * 1000), self._freeze, mode)

    def _freeze(self, mode: str):
        frame = capture.grab_root()
        if frame is None:
            self._capturing = False
            self.show()
            self.set_status("Capture failed - could not grab the root window")
            return False
        self._frame = frame
        if mode == "fullscreen":
            self._capture_done(Rect(0, 0, frame.get_width(), frame.get_height()))
        else:
            FreezeOverlay(frame).run(self._capture_done)
        return False

    def _capture_done(self, rect: Rect | None):
        self._capturing = False
        if rect is not None:
            pix = capture.crop(self._frame, rect)
        if rect is None or pix is None:
            self.show()
            self.set_status("Capture cancelled")
            return
        self._capture = pix
        self._saved_path = None
        w, h = pix.get_width(), pix.get_height()
        self._docsub.set_text(f"region {w}\u00d7{h} - unsaved")
        self._summary.set_text(self._capture_summary())
        self._canvas.queue_draw()
        self.show()
        self.set_status(f"Captured {w}\u00d7{h}")

    def _capture_summary(self) -> str:
        if self._capture is None:
            return "no capture"
        w, h = self._capture.get_width(), self._capture.get_height()
        text = f"{w}\u00d7{h} · PNG · 1 layer"
        if self._saved_path is not None:
            text += f" · saved {self._saved_path.name}"
        return text

    def _profile(self, name: str):
        if name == "Region":
            self._start_capture("region")
        elif name == "Full screen":
            self._start_capture("fullscreen")
        elif name == "Delayed 3 s":
            self._start_capture("region", delay_s=3)
        elif name == "Window":
            self.set_status("Window snapping lands with the v1 phase-3 geometry port")
        else:
            self.set_status(f"{name} capture is scheduled (see STUDIO-EDITOR-SPEC section 5)")

    def _build_left_rail(self):
        rail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        rail.get_style_context().add_class("studio-rail")
        rail.set_size_request(216, -1)
        rail.set_margin_start(8); rail.set_margin_end(8)
        rail.set_margin_top(8); rail.set_margin_bottom(8)

        cap = Gtk.Label(label="CAPTURE PROFILES", halign=Gtk.Align.START)
        cap.get_style_context().add_class("sect"); cap.get_style_context().add_class("muted")
        rail.append(cap)

        profiles = Gtk.FlowBox()
        profiles.set_min_children_per_line(3); profiles.set_max_children_per_line(3)
        profiles.set_column_spacing(4); profiles.set_row_spacing(4)
        profiles.set_homogeneous(True)
        for name, icon in PROFILE_ICONS.items():
            b = _icon_button(icon, f"{name} capture", 20)
            b.connect("clicked", lambda _b, n=name: self._profile(n))
            profiles.insert(b, -1)
        rail.append(profiles)

        tools = Gtk.Label(label="TOOLS", halign=Gtk.Align.START)
        tools.get_style_context().add_class("sect"); tools.get_style_context().add_class("muted")
        rail.append(tools)

        grid = Gtk.FlowBox()
        grid.set_min_children_per_line(4); grid.set_max_children_per_line(4)
        grid.set_column_spacing(4); grid.set_row_spacing(4)
        grid.set_homogeneous(True)
        for name, icon in TOOL_ICONS.items():
            grid.insert(_icon_button(icon, f"{name} tool (annotation tools land next milestone)", 20), -1)
        rail.append(grid)
        return rail

    def _build_center(self):
        center = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        center.set_hexpand(True); center.set_vexpand(True)

        opts = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        opts.get_style_context().add_class("studio-options")
        opts.set_margin_start(12); opts.set_margin_end(12)
        opts.set_margin_top(6); opts.set_margin_bottom(6)
        opts.append(Gtk.Label(label="Arrow (options bar - content per active tool)"))
        center.append(opts)

        canvas = Gtk.DrawingArea()
        canvas.set_hexpand(True); canvas.set_vexpand(True)
        canvas.set_draw_func(self._draw_canvas)
        self._canvas = canvas
        center.append(canvas)
        return center

    def _draw_canvas(self, area, cr, w, h):
        # checkerboard page; the capture draws fitted on top (zoom model later)
        cr.set_source_rgb(0.102, 0.122, 0.145)
        cr.paint()
        cr.set_source_rgb(0.149, 0.165, 0.188)
        step = 16
        for y in range(0, h, step):
            for x in range(0, w, step * 2):
                cr.rectangle(x + (y // step % 2) * step, y, step, step)
        cr.fill()
        if self._capture is None:
            return
        pw, ph = self._capture.get_width(), self._capture.get_height()
        if pw <= 0 or ph <= 0:
            return
        scale = min(w / pw, h / ph)
        dw, dh = pw * scale, ph * scale
        cr.save()
        cr.translate((w - dw) / 2, (h - dh) / 2)
        cr.scale(scale, scale)
        cr.rectangle(0, 0, pw, ph)
        cr.clip()
        Gdk.cairo_set_source_pixbuf(cr, self._capture, 0, 0)
        cr.paint()
        cr.restore()

    def _build_right_panels(self):
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right.get_style_context().add_class("studio-panels")
        right.set_size_request(280, -1)
        right.set_margin_start(8); right.set_margin_end(8)
        right.set_margin_top(8); right.set_margin_bottom(8)

        self._panel_stack = Gtk.Stack(); self._panel_stack.set_vexpand(True)
        self._panel_stack.add_named(self._page_label("Layers - annotation object model (phase 12/15)"), "layers")
        self._panel_stack.add_named(self._page_label("Captures - versions of this image (library, phase 6)"), "captures")
        self._panel_stack.add_named(self._page_label("Props - active tool settings"), "props")
        right.append(self._panel_stack)

        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        bar.set_halign(Gtk.Align.CENTER)
        for name, page in (("Layers", "layers"), ("Captures", "captures"), ("Props", "props")):
            b = _icon_button(PANEL_ICONS[name], f"{name} panel", 16)
            b.set_hexpand(True)
            b.connect("clicked", lambda _b, p=page: self._panel_stack.set_visible_child_name(p))
            bar.append(b)
        right.append(bar)
        return right

    def _page_label(self, text):
        l = Gtk.Label(label=text); l.set_wrap(True)
        l.set_margin_start(12); l.set_margin_end(12); l.set_margin_top(12)
        return l

    def _build_action_bar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.get_style_context().add_class("studio-actionbar")
        bar.set_margin_start(12); bar.set_margin_end(12)
        bar.set_margin_top(8); bar.set_margin_bottom(8)

        group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        discard = _icon_button(
            "trash", "Discard - drop the current capture", 16, css=("icon-32", "icon-danger"),
            color=tokens.COLOR["error"],
        )
        discard.connect("clicked", lambda *_: self._discard())
        group.append(discard)
        group.append(_icon_button("stack", "Flatten - merge layers (phase 15)", 16))
        group.append(_icon_button("images", "Captures - versions of this image", 16))
        bar.append(group)

        spacer = Gtk.Box(); bar.append(spacer); spacer.set_hexpand(True)
        self._summary = Gtk.Label(label="no capture")
        self._summary.get_style_context().add_class("muted")
        self._summary.set_margin_start(8); self._summary.set_margin_end(8)
        bar.append(self._summary)

        copy = _icon_button("copy", "Copy to clipboard", 16)
        copy.connect("clicked", lambda *_: self._copy_clipboard())
        bar.append(copy)
        save = _icon_button(
            "download-simple", "Save PNG to the captures folder",
            14, css=("icon-24", "primary"), color=tokens.COLOR["on_accent"],
        )
        save.connect("clicked", lambda *_: self._save())
        bar.append(save)

        self._status = Gtk.Label(label="Ready")
        self._status.get_style_context().add_class("muted")
        self._status.set_margin_start(8)
        bar.append(self._status)
        return bar

    def _discard(self):
        if self._capture is None:
            self.set_status("Nothing to discard")
            return
        self._capture = None
        self._frame = None
        self._saved_path = None
        self._docsub.set_text("no capture yet")
        self._summary.set_text(self._capture_summary())
        self._canvas.queue_draw()
        self.set_status("Discarded")

    def _copy_clipboard(self):
        if self._capture is None:
            self.set_status("Nothing to copy - capture first")
            return
        texture = Gdk.Texture.new_for_pixbuf(self._capture)
        clipboard = self.get_display().get_clipboard()
        try:
            clipboard.set_texture(texture)
        except AttributeError:
            clipboard.set(Gdk.ContentProvider.new_for_texture(texture))
        self.set_status("Copied to clipboard")

    def _save(self):
        if self._capture is None:
            self.set_status("Nothing to save - capture first")
            return
        folder = Path(self.settings.screenshot_path)
        self._saved_path = capture.save_png(self._capture, folder)
        self._docsub.set_text(self._saved_path.name)
        self._summary.set_text(self._capture_summary())
        self.set_status(f"Saved {self._saved_path}")

    def set_status(self, text: str):
        self._status.set_text(text)
