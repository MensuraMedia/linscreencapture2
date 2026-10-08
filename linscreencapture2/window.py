"""StudioWindow - the Studio Editor shell (GTK4).

Formation reproduced from mockup s044 (docs/design/, DOM in linshot3
redesign-2026) under STUDIO-EDITOR-SPEC.md sections 2-3 and the
DESIGN-CONTRACT r027 items, with operator-law overrides: r037 (every
button is an icon button; labels live in tooltips; 4px-grid evenness)
and r034 (no pills - radius 6/8/16; primaries 24px; "Captures" naming).

Theming via the vendored lintheme kit; APP_CSS installs at USER priority
after apply.install (D10). Capture pixels via core.capture (D6).
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gio, GLib, Gtk

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

C = tokens.COLOR  # single source: Graphite Night tokens

# contract #9: the fixed 12-color content palette (identical across themes)
CONTENT_COLORS = [
    "#e5484d", "#f76b15", "#ffb224", "#46a758", "#00a2c7", "#0091ff",
    "#6e56cf", "#d6409f", "#e58fb1", "#ffffff", "#85909b", "#1b1b1b",
]

# the kit substitutes token values in Python (GTK 4.14 has no CSS var())
# GTK CSS paints only: layout (spacing/size/alignment) is widget properties
APP_CSS = f"""
.studio-header {{ border-bottom: 1px solid {C['border']}; }}
.studio-options {{ border-bottom: 1px solid {C['border']}; }}
.studio-rail {{ border-right: 1px solid {C['border']}; }}
.studio-panels {{ border-left: 1px solid {C['border']}; }}
.studio-actionbar {{ border-top: 1px solid {C['border']}; }}

.sect {{ font-size: 11px; letter-spacing: 0.08em; }}

/* header doc block + stateful chip (contract #6, s044 hdr) */
.docsub {{ color: {C['text_muted']}; font-size: 12px; }}
.chip {{
  border-radius: 6px; padding: 4px 10px;
  background-color: {C['surface']}; border: 1px solid {C['border']};
  font-size: 12px;
}}
.chip .dot {{ border-radius: 999px; min-width: 8px; min-height: 8px; }}
.chip.ok {{ color: {C['ok']}; }}
.chip.ok .dot {{ background-color: {C['ok']}; }}
.chip.busy {{ color: {C['busy']}; }}
.chip.busy .dot {{ background-color: {C['busy']}; }}
.chip.attention {{ color: {C['attention']}; }}
.chip.attention .dot {{ background-color: {C['attention']}; }}

/* zoom control: tint container, radius 8 (spec section 2) */
.zoom {{
  border-radius: 8px; background-color: {C['surface']}; padding: 2px;
}}
.zoom .zv {{
  font-size: 12px; font-variant-numeric: tabular-nums;
  color: {C['text']};
}}

/* icon buttons (r037 law) */
.icon-btn {{ padding: 0; border-radius: 6px; }}
.icon-32 {{ min-width: 32px; min-height: 32px; }}
.icon-24 {{ min-width: 24px; min-height: 24px; }}
.icon-24.primary {{ background-color: {C['accent']}; }}
.icon-24.primary:hover {{ background-color: {C['accent_hover']}; }}
.icon-danger {{ color: {C['error']}; }}
/* active tool/profile: accent fill + on-accent icon (contract #3/#11) */
.icon-btn.active {{ background-color: {C['accent']}; }}
.icon-btn.active:hover {{ background-color: {C['accent_hover']}; }}

/* profile rows: 6 rows, 40px, active raised (spec section 3) */
.pirow {{ min-height: 40px; padding: 0 8px; border-radius: 6px; }}
.pirow.active {{ background-color: {C['surface_hover']}; }}

.toolcell {{ min-width: 40px; min-height: 40px; }}

/* color well: foreground over background (spec section 3) */
.colorwell {{ margin-top: 8px; }}

/* options bar (s044 optbar): segments, swatches, numerics */
.seg {{
  background-color: {C['surface']}; border-radius: 6px; padding: 2px;
}}
.seg button {{
  background-image: none; background-color: transparent; border: none;
  box-shadow: none; padding: 4px 10px; border-radius: 4px;
  font-size: 12px; color: {C['text_muted']}; min-height: 0;
}}
.seg button:hover {{ background-color: {C['surface_hover']}; color: {C['text']}; }}
.seg button.sel {{ background-color: {C['accent']}; color: {C['on_accent']}; }}
.sw {{
  min-width: 20px; min-height: 20px; border-radius: 3px;
  border: 1px solid {C['border']}; padding: 0;
}}
.sw.sel {{ outline: 2px solid {C['accent']}; outline-offset: 1px; }}
.numeric {{
  font-size: 12px; font-variant-numeric: tabular-nums;
  color: {C['text']}; background-color: {C['surface']};
  border-radius: 6px; padding: 4px 8px;
}}
.toggle {{
  background-image: none; background-color: transparent; border: none;
  box-shadow: none; padding: 4px 8px; border-radius: 6px; font-size: 12px;
  color: {C['text_muted']}; min-height: 0;
}}
.toggle:checked {{ color: {C['text']}; background-color: {C['surface']}; }}

/* right panels: top tabs (s044 ptabs), layer rows, footer */
.ptab {{
  background-image: none; background-color: transparent; border: none;
  box-shadow: none; padding: 6px 12px; font-size: 13px;
  color: {C['text_muted']}; border-bottom: 2px solid transparent;
  border-radius: 0; min-height: 0;
}}
.ptab.sel {{ color: {C['text']}; border-bottom-color: {C['accent']}; }}
.lrow {{ padding: 6px 8px; }}
.lthumb {{
  min-width: 24px; min-height: 20px; border-radius: 3px;
  background-color: {C['surface_hover']}; border: 1px solid {C['border']};
}}
.lkind {{
  font-size: 10px; color: {C['text_muted']}; border: 1px solid {C['border']};
  border-radius: 4px; padding: 1px 4px;
}}
.qs-sw {{
  min-width: 24px; min-height: 24px; border-radius: 6px; padding: 0;
  border: 1px solid {C['border']};
}}
.badge {{
  border-radius: 999px; background-color: {C['error']}; color: {C['bg']};
  min-width: 20px; min-height: 20px; font-size: 12px; font-weight: 600;
}}
.mini {{
  border: 1px solid {C['border']}; border-radius: 6px; background-color: {C['bg']};
}}

/* canvas zoom HUD chip (spec section 3: 28px, radius 6) */
.zoomhud {{
  background-color: {C['surface']}; border: 1px solid {C['border']};
  border-radius: 6px; padding: 4px 10px; font-size: 12px;
}}
.zoomhud b {{ color: {C['text']}; font-weight: 600; }}
""".encode()

PROFILE_META = {
    "Region": ("crop", "frozen"),
    "Window": ("app-window", "snaps"),
    "Full screen": ("monitor", "instant"),
    "Scrolling": ("arrows-out-line-vertical", "beta"),
    "Delayed 3 s": ("timer", "menu capture"),
    "Pin to screen": ("push-pin", "always-on-top"),
}

# tool groups per DESIGN-CONTRACT #4, extended with the Studio content tools
TOOL_GROUPS = [
    ("Select", [("Select", "cursor")]),
    ("Draw", [("Line", "pen-nib"), ("Arrow", "arrow-up-right"), ("Box", "square"),
              ("Circle", "circle"), ("Text", "text-t"), ("Pen", "pen"),
              ("Marker", "marker-circle")]),
    ("Redact", [("Blur", "circle-dashed"), ("Pixelate", "grid-four"),
                ("Fill", "paint-bucket")]),
    ("Content", [("Step", "number-circle-one"), ("Callout", "chat-teardrop-text")]),
    ("Transform", [("Crop", "crop"), ("Resize", "arrows-horizontal"),
                   ("Rotate", "arrow-clockwise"), ("Bright", "sun")]),
    ("Edit", [("Move", "arrows-out"), ("Dupe", "copy")]),
]

TOOL_NAMES = {name: icon for _, tools in TOOL_GROUPS for name, icon in tools}

QUICK_STYLES = [
    ("Arrow - bold red", "#e5484d"),
    ("Arrow - yellow marker", "#ffb224"),
    ("Box - success", "#46a758"),
    ("Callout - violet", "#6e56cf"),
]

PANEL_PAGES = {"Layers": ("stack", "layers"), "Captures": ("images", "captures"),
               "Props": ("sliders-horizontal", "props")}


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


def _hex_button(hexcolor: str, tooltip: str, css_class: str, px: int = 20) -> Gtk.Button:
    b = Gtk.Button()
    area = Gtk.DrawingArea()
    area.set_content_width(px - 2)
    area.set_content_height(px - 2)
    area.set_draw_func(lambda _a, cr, _w, _h: (
        cr.set_source_rgba(*(_hex_rgb(hexcolor))),
        cr.paint()))
    b.set_child(area)
    b.set_tooltip_text(tooltip)
    ctx = b.get_style_context()
    ctx.add_class(css_class)
    return b


def _hex_rgb(hexcolor: str):
    hexcolor = hexcolor.lstrip("#")
    r, g, b = (int(hexcolor[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (r, g, b, 1.0)


class StudioWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("LinScreenCapture - Studio Editor")
        self.set_default_size(1280, 800)
        self.set_size_request(720, 540)  # contract #14 minimum window
        apply.install(self)
        self._install_css()

        self.settings = Settings.load()
        self._frame = None  # whole-root frozen frame of the last capture
        self._capture = None  # cropped Base layer shown on the canvas
        self._saved_path: Path | None = None
        self._capturing = False
        self._active_profile = "Region"
        self._active_tool = "Arrow"  # s044 shows the Arrow tool active
        self._build()

    def _install_css(self):
        # the kit loads its CSS at USER priority, so app CSS must load at
        # USER priority too (after apply.install) or kit rules win ties (D10)
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
        self._set_chip("ready")

    # --- header (s044 hdr: doc block, chip, spacer, zoom, Capture) ------------

    def _build_header(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.get_style_context().add_class("studio-header")
        bar.get_style_context().add_class("lt-header")
        bar.set_margin_start(12); bar.set_margin_end(12)
        bar.set_margin_top(8); bar.set_margin_bottom(8)

        doc = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._doc_title = Gtk.Label(label="Untitled", halign=Gtk.Align.START)
        self._doc_title.get_style_context().add_class("title")
        self._docsub = Gtk.Label(label="Edit · 0 layers · unsaved changes",
                                 halign=Gtk.Align.START)
        self._docsub.get_style_context().add_class("docsub")
        doc.append(self._doc_title); doc.append(self._docsub)
        bar.append(doc)

        self._chip = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        chip_ctx = self._chip.get_style_context()
        chip_ctx.add_class("chip")
        self._chip_dot = Gtk.Box()
        self._chip_dot.get_style_context().add_class("dot")
        self._chip_word = Gtk.Label(label="Ready")
        self._chip.append(self._chip_dot); self._chip.append(self._chip_word)
        self._chip.set_margin_start(8)
        self._chip.set_valign(Gtk.Align.CENTER)
        self._chip.set_halign(Gtk.Align.START)
        self._chip.set_tooltip_text("All systems nominal - arm a capture profile")
        bar.append(self._chip)

        spacer = Gtk.Box(); bar.append(spacer); spacer.set_hexpand(True)

        zoom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        zoom.get_style_context().add_class("zoom")
        zoom.append(_icon_button("minus", "Zoom out (zoom model: HANDOFF 7.7)", 16))
        self._zoom_val = Gtk.Label(label="100%")
        self._zoom_val.get_style_context().add_class("zv")
        self._zoom_val.set_margin_start(8)
        self._zoom_val.set_margin_end(8)
        zoom.append(self._zoom_val)
        zoom.append(_icon_button("plus", "Zoom in (zoom model: HANDOFF 7.7)", 16))
        zoom.append(_icon_button("arrows-in", "Fit to window (zoom model: HANDOFF 7.7)", 16))
        bar.append(zoom)

        cap = _icon_button(
            "camera", "Capture - freeze the screen and select a region (PrintScreen)",
            14, css=("icon-24", "primary"), color=C["on_accent"],
        )
        cap.connect("clicked", lambda *_: self._start_capture("region"))
        bar.append(cap)
        return bar

    def _set_chip(self, state: str, detail: str | None = None):
        """Contract #6 vocabulary: ready / selecting / captured / can't-capture."""
        ctx = self._chip.get_style_context()
        for c in ("ok", "busy", "attention"):
            ctx.remove_class(c)
        words = {"ready": "Ready", "selecting": "Selecting",
                 "captured": "Captured", "cant": "Can't capture"}
        classes = {"ready": "ok", "selecting": "busy", "captured": "ok", "cant": "attention"}
        ctx.add_class(classes[state])
        self._chip_word.set_text(words[state])
        self._chip.set_tooltip_text(detail or words[state])

    def set_status(self, text: str):
        """Errors report via the attention chip; the tooltip carries the why."""
        self._set_chip("cant", text)

    # --- capture pipeline (v1 freeze-frame port) --------------------------------

    def _start_capture(self, mode: str, delay_s: int | None = None):
        """mode: "region" (overlay select) or "fullscreen" (whole root)."""
        if self._capturing:
            return
        if not capture.display_is_x11():
            self._set_chip("cant", "Capture needs X11 (Wayland portal: HANDOFF 7.9)")
            return
        self._capturing = True
        self.settings.capture_mode = 0 if mode == "region" else 3
        self.settings.save()
        if delay_s is None:
            delay_s = self.settings.capture_delay
        self._set_chip("selecting", "Freezing the screen")
        # hide first so the studio window never lands in the frozen frame
        self.hide()
        GLib.timeout_add(max(HIDE_SETTLE_MS, delay_s * 1000), self._freeze, mode)

    def _freeze(self, mode: str):
        frame = capture.grab_root()
        if frame is None:
            self._capturing = False
            self.show()
            self._set_chip("cant", "Could not grab the root window - capture dropped")
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
            self._set_chip("ready", "Capture cancelled - nothing changed")
            return
        self._capture = pix
        self._saved_path = None
        self._refresh_doc()
        self._summary.set_text(self._capture_summary())
        self._canvas.queue_draw()
        self._rebuild_layers()
        self.show()
        self._set_chip("captured", f"Captured {pix.get_width()}\u00d7{pix.get_height()}")

    def _layer_count(self) -> int:
        return 1 if self._capture is not None else 0

    def _refresh_doc(self):
        n = self._layer_count()
        title = str(self._saved_path.name) if self._saved_path else "Untitled"
        state = "saved" if self._saved_path else "unsaved changes"
        self._doc_title.set_text(title)
        self._docsub.set_text(f"Edit · {n} layer{'s' if n != 1 else ''} · {state}")

    def _capture_summary(self) -> str:
        if self._capture is None:
            return "no capture"
        w, h = self._capture.get_width(), self._capture.get_height()
        return f"{w} \u00d7 {h} · PNG · {self._layer_count()} layer · 100%"

    def _profile(self, name: str):
        if name == "Region":
            self._start_capture("region")
        elif name == "Full screen":
            self._start_capture("fullscreen")
        elif name == "Delayed 3 s":
            self._start_capture("region", delay_s=3)
        elif name == "Window":
            self._set_chip("cant", "Window snapping lands with the v1 phase-3 geometry port")
        else:
            self._set_chip("cant", f"{name} capture is scheduled (HANDOFF 7)")

    # --- left rail (s044 left: profiles rows, tools, color well) ----------------

    def _build_left_rail(self):
        rail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        rail.get_style_context().add_class("studio-rail")
        rail.set_size_request(216, -1)
        rail.set_margin_start(8); rail.set_margin_end(8)
        rail.set_margin_top(8); rail.set_margin_bottom(8)

        cap = Gtk.Label(label="CAPTURE PROFILES", halign=Gtk.Align.START, xalign=0)
        cap.get_style_context().add_class("sect"); cap.get_style_context().add_class("muted")
        rail.append(cap)

        self._profile_buttons: dict[str, Gtk.Button] = {}
        for name, (icon, meta) in PROFILE_META.items():
            b = _icon_button(icon, f"{name} capture \u2014 {meta}", 20, css=("icon-32", "pirow"))
            b.set_halign(Gtk.Align.START)
            b.connect("clicked", lambda _b, n=name: self._profile(n))
            self._profile_buttons[name] = b
            rail.append(b)
        self._mark_active_profile()

        tools = Gtk.Label(label="TOOLS", halign=Gtk.Align.START, xalign=0)
        tools.get_style_context().add_class("sect"); tools.get_style_context().add_class("muted")
        rail.append(tools)

        self._tool_buttons: dict[str, Gtk.Button] = {}
        for gi_, (group, tools) in enumerate(TOOL_GROUPS):
            if gi_ > 0:
                rail.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
            grid = Gtk.Grid(row_spacing=4, column_spacing=4)  # 2 columns per spec s3
            for ti, (name, icon) in enumerate(tools):
                b = _icon_button(icon, f"{group}: {name} tool", 20, css=("icon-32", "toolcell"))
                b.connect("clicked", lambda _b, n=name: self._pick_tool(n))
                self._tool_buttons[name] = b
                grid.attach(b, ti % 2, ti // 2, 1, 1)
            rail.append(grid)
        self._mark_active_tool()

        spacer = Gtk.Box()
        spacer.set_vexpand(True)  # pins the color well to the rail bottom
        rail.append(spacer)
        well = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        well.get_style_context().add_class("colorwell")
        fg = _hex_button(CONTENT_COLORS[0], "Foreground color - content palette",
                         "sw", 24)
        bg = _hex_button(CONTENT_COLORS[9], "Background color - content palette",
                         "sw", 24)
        well.append(fg); well.append(bg)
        swap = _icon_button("swap", "Swap foreground and background (X)", 16)
        well.append(swap)
        rail.append(well)
        return rail

    def _mark_active_profile(self):
        for name, b in self._profile_buttons.items():
            ctx = b.get_style_context()
            ctx.remove_class("active")
            if name == self._active_profile:
                ctx.add_class("active")

    def _mark_active_tool(self):
        for name, b in self._tool_buttons.items():
            ctx = b.get_style_context()
            ctx.remove_class("active")
            if name == self._active_tool:
                icon = Gtk.Image.new_from_paintable(Gdk.Texture.new_for_pixbuf(
                    icons.pixbuf(TOOL_NAMES[name], 20, C["on_accent"])))
                b.set_child(icon)
                ctx.add_class("active")
            else:
                b.set_child(Gtk.Image.new_from_paintable(
                    Gdk.Texture.new_for_pixbuf(icons.pixbuf(TOOL_NAMES[name], 20))))

    def _pick_tool(self, name: str):
        self._active_tool = name
        self._mark_active_tool()
        self._refresh_options_bar()

    # --- center (s044 optbar + canvaswrap + zoomhud) ------------------------------

    def _build_center(self):
        center = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        center.set_hexpand(True); center.set_vexpand(True)

        self._options_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self._options_bar.get_style_context().add_class("studio-options")
        self._options_bar.set_margin_start(12); self._options_bar.set_margin_end(12)
        self._options_bar.set_margin_top(6); self._options_bar.set_margin_bottom(6)
        center.append(self._options_bar)
        self._refresh_options_bar()

        overlay = Gtk.Overlay()
        overlay.set_vexpand(True)
        canvas = Gtk.DrawingArea()
        canvas.set_hexpand(True); canvas.set_vexpand(True)
        canvas.set_draw_func(self._draw_canvas)
        self._canvas = canvas
        overlay.set_child(canvas)

        hud = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        hud.get_style_context().add_class("zoomhud")
        pct = Gtk.Label(); pct.get_style_context().add_class("zv")
        pct.set_markup("<b>100%</b>")
        hud.append(pct)
        hud.append(Gtk.Label(label="· Fit"))
        hud.set_halign(Gtk.Align.START); hud.set_valign(Gtk.Align.END)
        hud.set_margin_start(16); hud.set_margin_bottom(16)
        overlay.add_overlay(hud)
        center.append(overlay)
        return center

    def _refresh_options_bar(self):
        """s044 optbar formation for the active tool (content registry: E1)."""
        bar = self._options_bar
        self._clear(bar)
        name = self._active_tool
        icon = Gtk.Image.new_from_paintable(Gdk.Texture.new_for_pixbuf(
            icons.pixbuf(TOOL_NAMES.get(name, "cursor"), 20)))
        bar.append(icon)
        label = Gtk.Label(label=name)
        label.get_style_context().add_class("lt-strong")
        bar.append(label)

        if name in ("Arrow", "Line", "Pen", "Marker"):
            bar.append(self._segment(("Thin", "Body", "Chunky"), 0,
                                     f"{name} stroke weight"))
        if name in ("Arrow", "Line", "Box", "Circle", "Text", "Pen", "Step",
                    "Callout", "Fill", "Marker"):
            sw = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            sw.get_style_context().add_class("swrow")
            for i, hexc in enumerate(CONTENT_COLORS):
                b = _hex_button(hexc, f"Content color {hexc}", "sw")
                if i == 0:
                    b.get_style_context().add_class("sel")
                sw.append(b)
            bar.append(sw)
        if name in ("Arrow", "Box", "Circle", "Text", "Step", "Callout"):
            bar.append(self._toggle("Shadow", True, f"{name} drop shadow"))
        if name == "Arrow":
            num = Gtk.Label(label="Head 1.0\u00d7")
            num.get_style_context().add_class("numeric")
            bar.append(num)
            bar.append(self._segment(("Square", "Rounded"), 1, f"{name} tail shape"))
        if name == "Text":
            num = Gtk.Label(label="Body 16px")
            num.get_style_context().add_class("numeric")
            bar.append(num)
        if name in ("Blur", "Pixelate"):
            bar.append(self._segment(("2", "4", "6", "8"), 1, f"{name} intensity"))
        if name == "Step":
            num = Gtk.Label(label="Next \u2116 1")
            num.get_style_context().add_class("numeric")
            bar.append(num)
        # keep the bar airy: controls stay left-aligned per s044
        return

    def _segment(self, options: tuple[str, ...], selected: int, tooltip: str) -> Gtk.Box:
        seg = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        seg.get_style_context().add_class("seg")
        for i, opt in enumerate(options):
            b = Gtk.Button(label=opt)
            b.set_tooltip_text(f"{tooltip}: {opt}")
            if i == selected:
                b.get_style_context().add_class("sel")
            seg.append(b)
        return seg

    def _toggle(self, label: str, checked: bool, tooltip: str) -> Gtk.ToggleButton:
        t = Gtk.ToggleButton(label=label, active=checked)
        t.set_tooltip_text(tooltip)
        t.get_style_context().add_class("toggle")
        return t

    @staticmethod
    def _clear(box: Gtk.Box):
        child = box.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            box.remove(child)
            child = nxt

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

    # --- right panels (s044 right: ptabs top, pbody, pfoot) -----------------------

    def _build_right_panels(self):
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        right.get_style_context().add_class("studio-panels")
        right.set_size_request(280, -1)
        right.set_margin_start(8); right.set_margin_end(8)
        right.set_margin_top(8); right.set_margin_bottom(8)

        tabs = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        tabs.set_halign(Gtk.Align.FILL)
        self._panel_stack = Gtk.Stack()
        self._panel_stack.set_vexpand(True)
        self._panel_stack.set_transition_type(Gtk.StackTransitionType.NONE)
        self._panel_tabs: dict[str, Gtk.Button] = {}
        for i, (name, (icon, page)) in enumerate(PANEL_PAGES.items()):
            if i > 0:
                tabs.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
            b = _icon_button(icon, f"{name} panel", 16)
            b.get_style_context().add_class("ptab")
            b.set_hexpand(True)
            b.connect("clicked", lambda _b, p=name: self._show_panel(p))
            self._panel_tabs[name] = b
            tabs.append(b)
        right.append(tabs)
        right.append(self._panel_stack)

        self._panel_stack.add_named(self._build_layers_page(), "layers")
        self._panel_stack.add_named(self._page_label(
            "Captures - versions of this image (library-backed list lands with"
            " the panels milestone; the catalog itself is read-only per D2)"),
            "captures")
        self._panel_stack.add_named(self._page_label(
            "Props - active tool settings (per-tool card: colour, width,"
            " shadow, usage note)"), "props")

        right.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        right.append(self._build_panel_footer())
        self._show_panel("Layers")
        return right

    def _show_panel(self, name: str):
        self._panel_stack.set_visible_child_name(PANEL_PAGES[name][1])
        for n, b in self._panel_tabs.items():
            ctx = b.get_style_context()
            ctx.remove_class("sel")
            if n == name:
                ctx.add_class("sel")

    def _build_layers_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        page.set_margin_top(8)
        page.set_margin_start(4); page.set_margin_end(4)
        self._layers_box = page
        self._rebuild_layers()
        return page

    def _rebuild_layers(self):
        """s044 lrow formation: thumb · name · kind chip · eye (top = top z)."""
        self._clear(self._layers_box)
        if self._capture is None:
            empty = Gtk.Label(label="No capture yet - the Base layer appears here",
                              wrap=True, xalign=0)
            empty.get_style_context().add_class("muted")
            empty.set_margin_top(8); empty.set_margin_start(8); empty.set_margin_end(8)
            self._layers_box.append(empty)
            return
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.get_style_context().add_class("lrow")
        thumb = Gtk.Box()
        thumb.get_style_context().add_class("lthumb")
        row.append(thumb)
        name = Gtk.Label(label="Base capture", xalign=0)
        name.set_hexpand(True)
        row.append(name)
        kind = Gtk.Label(label="IMG")
        kind.get_style_context().add_class("lkind")
        row.append(kind)
        eye = _icon_button("eye", "Toggle layer visibility", 14, css=("icon-24",))
        eye.set_sensitive(False)  # visibility toggles land with the object model
        row.append(eye)
        self._layers_box.append(row)

    def _build_panel_footer(self):
        """s044 pfoot: quick styles, steps next-No, navigator minimap."""
        foot = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        foot.set_margin_top(8); foot.set_margin_bottom(8)

        qs_label = Gtk.Label(label="QUICK STYLES", halign=Gtk.Align.START, xalign=0)
        qs_label.get_style_context().add_class("sect"); qs_label.get_style_context().add_class("muted")
        foot.append(qs_label)
        qs = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for name, hexc in QUICK_STYLES:
            qs.append(_hex_button(hexc, name, "qs-sw", 24))
        foot.append(qs)

        steps = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        badge = Gtk.Label(label="1")
        badge.get_style_context().add_class("badge")
        steps.append(badge)
        step_text = Gtk.Label(label="Steps - next \u2116, auto-increment", xalign=0)
        step_text.get_style_context().add_class("muted")
        steps.append(step_text)
        foot.append(steps)

        nav_label = Gtk.Label(label="NAVIGATOR", halign=Gtk.Align.START, xalign=0)
        nav_label.get_style_context().add_class("sect"); nav_label.get_style_context().add_class("muted")
        foot.append(nav_label)
        mini_wrap = Gtk.Box()
        mini_wrap.get_style_context().add_class("mini")
        mini = Gtk.DrawingArea()
        mini.set_content_height(72)
        mini.set_hexpand(True)
        mini.set_draw_func(self._draw_minimap)
        mini_wrap.set_margin_start(8); mini_wrap.set_margin_end(8)
        mini_wrap.append(mini)
        foot.append(mini_wrap)
        return foot

    def _draw_minimap(self, _area, cr, w, h):
        # navigator minimap: scaled capture once a capture exists (zoom phase
        # wires live sync); checker placeholder until then
        cr.set_source_rgb(0.110, 0.122, 0.137)
        cr.paint()
        if self._capture is None:
            return
        pw, ph = self._capture.get_width(), self._capture.get_height()
        scale = min(w / pw, h / ph)
        dw, dh = pw * scale, ph * scale
        cr.save()
        cr.translate((w - dw) / 2, (h - dh) / 2)
        cr.scale(scale, scale)
        Gdk.cairo_set_source_pixbuf(cr, self._capture, 0, 0)
        cr.paint()
        cr.restore()

    def _page_label(self, text):
        l = Gtk.Label(label=text); l.set_wrap(True); l.set_xalign(0)
        l.set_margin_start(12); l.set_margin_end(12); l.set_margin_top(12)
        return l

    # --- action bar (s044 ab: Discard · Flatten · Captures-menu · summary ·
    #     Copy · Save; the status lives in the header chip only) -------------------

    def _build_action_bar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.get_style_context().add_class("studio-actionbar")
        bar.set_margin_start(12); bar.set_margin_end(12)
        bar.set_margin_top(8); bar.set_margin_bottom(8)

        discard = _icon_button(
            "trash", "Discard - drop the current capture", 16,
            css=("icon-32", "icon-danger"), color=C["error"],
        )
        discard.connect("clicked", lambda *_: self._discard())
        bar.append(discard)
        bar.append(_icon_button("stack", "Flatten - merge layers (phase 15)", 16))

        captures = Gtk.MenuButton()
        captures.set_tooltip_text("Captures - versions and the captures folder")
        cap_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        cap_box.append(Gtk.Image.new_from_paintable(Gdk.Texture.new_for_pixbuf(
            icons.pixbuf("images", 16))))
        cap_box.append(Gtk.Image.new_from_paintable(Gdk.Texture.new_for_pixbuf(
            icons.pixbuf("caret-down", 12))))
        captures.set_child(cap_box)
        ctx = captures.get_style_context()
        ctx.add_class("lt-icon-btn"); ctx.add_class("icon-btn"); ctx.add_class("icon-32")
        popover = Gtk.Popover()
        pop_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        pop_box.set_margin_start(8); pop_box.set_margin_end(8)
        pop_box.set_margin_top(8); pop_box.set_margin_bottom(8)
        open_btn = Gtk.Button(label="Open captures folder")
        open_btn.connect("clicked", lambda *_: self._open_captures_folder())
        pop_box.append(open_btn)
        later = Gtk.Button(label="Re-open editable (phase 6)", sensitive=False)
        later.set_tooltip_text("Re-open a saved capture with its layers - scheduled")
        pop_box.append(later)
        popover.set_child(pop_box)
        captures.set_popover(popover)
        bar.append(captures)

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
            14, css=("icon-24", "primary"), color=C["on_accent"],
        )
        save.connect("clicked", lambda *_: self._save())
        bar.append(save)
        return bar

    def _open_captures_folder(self):
        folder = Path(self.settings.screenshot_path)
        launcher = Gtk.FileLauncher()
        launcher.set_file(Gio.File.new_for_path(str(folder)))
        launcher.launch(self, None, None, None)

    def _discard(self):
        if self._capture is None:
            self._set_chip("ready", "Nothing to discard")
            return
        self._capture = None
        self._frame = None
        self._saved_path = None
        self._refresh_doc()
        self._summary.set_text(self._capture_summary())
        self._canvas.queue_draw()
        self._rebuild_layers()
        self._set_chip("ready", "Capture discarded")

    def _copy_clipboard(self):
        if self._capture is None:
            self._set_chip("cant", "Nothing to copy - capture first")
            return
        texture = Gdk.Texture.new_for_pixbuf(self._capture)
        clipboard = self.get_display().get_clipboard()
        try:
            clipboard.set_texture(texture)
        except AttributeError:
            clipboard.set(Gdk.ContentProvider.new_for_texture(texture))
        self._set_chip("captured", "Copied to clipboard")

    def _save(self):
        if self._capture is None:
            self._set_chip("cant", "Nothing to save - capture first")
            return
        folder = Path(self.settings.screenshot_path)
        self._saved_path = capture.save_png(self._capture, folder)
        self._refresh_doc()
        self._summary.set_text(self._capture_summary())
        self._set_chip("captured", f"Saved {self._saved_path.name}")
