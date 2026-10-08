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

.sect {{ font-size: 10px; letter-spacing: 0.04em; }}
.grouplabel {{ font-size: 10px; letter-spacing: 0.06em; }}

/* header doc block + stateful chip (contract #6, s044 hdr) */
.docsub {{ color: {C['text_muted']}; font-size: 12px; }}
.chip {{
  border-radius: 6px; padding: 4px 8px;
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
/* MenuButton carries an internal theme-padded button: size IT to the same
   24px square or flyout anchors render larger than plain buttons (r050) */
menubutton.icon-btn > button {{ padding: 0; min-width: 24px; min-height: 24px; }}
menubutton.icon-btn > button > box {{ min-width: 16px; min-height: 16px; }}
.icon-24.primary {{ background-color: {C['accent']}; }}
.icon-24.primary:hover {{ background-color: {C['accent_hover']}; }}
.icon-danger {{ color: {C['error']}; }}
/* active tool/profile: accent fill + on-accent icon (contract #3/#11) */
.icon-btn.active {{ background-color: {C['accent']}; }}
.icon-btn.active:hover {{ background-color: {C['accent_hover']}; }}

/* profile rows: 6 rows, 40px, active raised (spec section 3) */
.pirow {{ min-height: 24px; padding: 0; border-radius: 6px; }}
.pirow.active {{ background-color: {C['surface_hover']}; }}

.toolcell {{ min-width: 24px; min-height: 24px; }}

/* color well: foreground over background (spec section 3) */
.colorwell {{ margin-top: 8px; }}
.swp {{ min-width: 18px; min-height: 18px; border-radius: 4px; padding: 0;
  border: 1px solid {C['border']}; }}
.swp.sel {{ outline: 2px solid {C['accent']}; outline-offset: 1px; }}
.fgcircle {{ border-radius: 999px; min-width: 20px; min-height: 20px;
  padding: 0; border: 1px solid {C['border']}; }}
.hexentry {{ font-size: 12px; font-family: monospace; padding: 4px 6px; }}

/* hover flyouts: flat dark-gray #141414, minimal chrome (r056) */
popover.hoverfly > contents {{
  background-color: #141414; border: none; box-shadow: none;
  border-radius: 4px; padding: 2px;
}}
popover.hoverfly > arrow {{ background-color: #141414; border: none; }}

/* options bar (s044 optbar): segments, swatches, numerics */
.seg {{
  background-color: {C['surface']}; border-radius: 6px; padding: 2px;
}}
.seg button {{
  background-image: none; background-color: transparent; border: none;
  box-shadow: none; padding: 4px 8px; border-radius: 4px;
  font-size: 12px; color: {C['text_muted']}; min-height: 0;
}}
.seg button:hover {{ background-color: {C['surface_hover']}; color: {C['text']}; }}
.seg button.sel {{ background-color: {C['accent']}; color: {C['on_accent']}; }}
.sw {{
  min-width: 18px; min-height: 18px; border-radius: 3px;
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
  box-shadow: none; padding: 4px 8px; font-size: 13px;
  color: {C['text_muted']}; border-bottom: 2px solid transparent;
  border-radius: 0; min-height: 0;
}}
.ptab.sel {{ color: {C['text']}; border-bottom-color: {C['accent']}; }}
.lrow {{ padding: 4px 8px; }}
.lthumb {{
  min-width: 24px; min-height: 20px; border-radius: 3px;
  background-color: {C['surface_hover']}; border: 1px solid {C['border']};
}}
.lkind {{
  font-size: 10px; color: {C['text_muted']}; border: 1px solid {C['border']};
  border-radius: 4px; padding: 1px 4px;
}}
.qs-sw {{
  min-width: 18px; min-height: 18px; border-radius: 6px; padding: 0;
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
  border-radius: 6px; padding: 4px 8px; font-size: 12px;
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

# single-word hover captions (r055)
PROFILE_SHORT = {
    "Region": "Region", "Window": "Window", "Full screen": "Fullscreen",
    "Scrolling": "Scrolling", "Delayed 3 s": "Delayed",
    "Pin to screen": "Pin",
}

# single-word quick-style captions (r055)
STYLE_SHORT = {
    "Arrow - bold red": "Red", "Arrow - yellow marker": "Yellow",
    "Box - success": "Green", "Callout - violet": "Violet",
}

QUICK_STYLES = [
    ("Arrow - bold red", "#e5484d"),
    ("Arrow - yellow marker", "#ffb224"),
    ("Box - success", "#46a758"),
    ("Callout - violet", "#6e56cf"),
]

PANEL_PAGES = {"Layers": ("stack", "layers"), "Captures": ("images", "captures"),
               "Props": ("sliders-horizontal", "props")}


def _icon_image(name: str, px: int, color: str | None = None) -> Gtk.Image:
    """Crisp icon: raster at 2x and constrain to the display size - the
    Image never stretches the texture, which is what blurred buttons (r044)."""
    img = Gtk.Image.new_from_paintable(
        Gdk.Texture.new_for_pixbuf(icons.pixbuf(name, px * 2, color)))
    img.set_size_request(px, px)
    return img


def _icon_button(name: str, tooltip: str, icon_px: int = 16,
                 css: tuple[str, ...] = ("icon-24",),
                 color: str | None = None) -> Gtk.Button:
    """Square icon button; the label is the tooltip (r037 law).
    24px square is the standard size (r043); icons render crisp (r044)."""
    b = Gtk.Button()
    b.set_child(_icon_image(name, icon_px, color))
    b.set_tooltip_text(tooltip)
    ctx = b.get_style_context()
    ctx.add_class("lt-icon-btn")
    ctx.add_class("icon-btn")
    for c in css:
        ctx.add_class(c)
    return b


# representative icon per tool group (collapsed-pane consolidation, r044)
GROUP_ICONS = {
    "Select": "cursor", "Draw": "pen", "Redact": "drop-half",
    "Content": "chat-teardrop-text", "Transform": "arrow-clockwise",
    "Edit": "arrows-out",
}


def _flyout_button(icon: str, tooltip: str, buttons: list[Gtk.Button],
                   css: tuple[str, ...] = ("icon-24",)) -> Gtk.MenuButton:
    """Consolidated button: hover pops out the full group (r044 collapse law).
    Icons per the vendored Phosphor set only."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    box.set_margin_start(2); box.set_margin_end(2)
    box.set_margin_top(2); box.set_margin_bottom(2)
    for b in buttons:
        box.append(b)
    return _flyout_box(icon, tooltip, box, css)


def _flyout_box(icon: str, tooltip: str, box: Gtk.Box,
                css: tuple[str, ...] = ("icon-24",)) -> Gtk.MenuButton:
    """Hover flyout with arbitrary content (r053: panel pages live here)."""
    pop = Gtk.Popover()
    pop.get_style_context().add_class("hoverfly")
    pop.set_child(box)
    pop.set_position(Gtk.PositionType.RIGHT)  # hover-expansion to the right
    mb = Gtk.MenuButton()
    mb.set_child(_icon_image(icon, 16))
    mb.set_popover(pop)
    mb.set_tooltip_text(tooltip)
    ctx = mb.get_style_context()
    ctx.add_class("lt-icon-btn"); ctx.add_class("icon-btn")
    for c in css:
        ctx.add_class(c)

    pending = {"src": None}

    def _open(*_):
        if pending["src"] is not None:
            GLib.source_remove(pending["src"])
            pending["src"] = None
        pop.popup()

    def _schedule_close(*_):
        if pending["src"] is not None:
            GLib.source_remove(pending["src"])
        pending["src"] = GLib.timeout_add(220, pop.popdown)

    motion = Gtk.EventControllerMotion()
    motion.connect("enter", _open)
    motion.connect("leave", _schedule_close)
    mb.add_controller(motion)
    inside = Gtk.EventControllerMotion()
    inside.connect("enter", _open)
    inside.connect("leave", _schedule_close)
    box.add_controller(inside)
    return mb


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


def _parse_hex(text: str):
    """'#6f19e6' / '6f1' -> (r, g, b) 0-255, else None (r051 picker)."""
    t = text.strip().lstrip("#")
    if len(t) == 3:
        t = "".join(c * 2 for c in t)
    if len(t) != 6:
        return None
    try:
        return tuple(int(t[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def _to_hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(rgb)


class StudioWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("LinScreenCapture - Studio Editor")
        self.set_default_size(960, 640)  # compact default (r043); min below
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
        self._zoom = 1.0  # stage shows captures at ORIGINAL size (r057)
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
        # Grid, not Box: pane columns hold their exact fixed width and the
        # canvas column absorbs all extra space (r047)
        middle = Gtk.Grid()
        middle.set_vexpand(True)
        root.append(middle)
        middle.attach(self._build_left_rail(), 0, 0, 1, 1)
        middle.attach(self._build_center(), 1, 0, 1, 1)
        middle.attach(self._build_right_panels(), 2, 0, 1, 1)
        # r052: no bottom action bar - its icons live in the left sidebar
        self._set_chip("ready")

    # --- header (s044 hdr: doc block, chip, spacer, zoom, Capture) ------------

    def _build_header(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        bar.get_style_context().add_class("studio-header")
        bar.get_style_context().add_class("lt-header")
        bar.set_margin_start(8); bar.set_margin_end(8)
        bar.set_margin_top(4); bar.set_margin_bottom(4)

        doc = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._doc_title = Gtk.Label(label="Untitled", halign=Gtk.Align.START)
        self._doc_title.get_style_context().add_class("title")
        self._docsub = Gtk.Label(label="Edit · 0 layers · unsaved changes",
                                 halign=Gtk.Align.START)
        self._docsub.get_style_context().add_class("docsub")
        doc.append(self._doc_title); doc.append(self._docsub)
        bar.append(doc)

        self._chip = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        chip_ctx = self._chip.get_style_context()
        chip_ctx.add_class("chip")
        self._chip_dot = Gtk.Box()
        self._chip_dot.get_style_context().add_class("dot")
        self._chip_word = Gtk.Label(label="Ready")
        self._chip.append(self._chip_dot); self._chip.append(self._chip_word)
        self._chip.set_margin_start(4)
        self._chip.set_valign(Gtk.Align.CENTER)
        self._chip.set_halign(Gtk.Align.START)
        self._chip.set_tooltip_text("All systems nominal - arm a capture profile")
        bar.append(self._chip)

        spacer = Gtk.Box(); bar.append(spacer); spacer.set_hexpand(True)

        zoom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        zoom.get_style_context().add_class("zoom")
        zoom.append(_icon_button("minus", "Out", 16))
        self._zoom_val = Gtk.Label(label="100%")
        self._zoom_val.get_style_context().add_class("zv")
        self._zoom_val.set_margin_start(8)
        self._zoom_val.set_margin_end(8)
        zoom.append(self._zoom_val)
        zoom.append(_icon_button("plus", "In", 16))
        zoom.append(_icon_button("arrows-in", "Fit", 16))
        bar.append(zoom)

        cap = _icon_button(
            "camera", "Capture",
            16, css=("icon-24", "primary"), color=C["on_accent"],
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

    # --- left rail (r044 flyouts; r046 fixed-pixel widths, >=5 icons wide) ------

    # pane widths are FIXED pixels (r046: collapse/expand never scale by
    # percentage): expanded fits >=5 icons per row; the left sidebar
    # collapses to exactly one 24px icon plus its 8px pane margins
    LEFT_W = 100        # r047: expanded sidebar is 100px - three 24px
    RIGHT_W = 100       # columns fill it accurately (hexpand cells)
    LEFT_COLLAPSED_W = 40   # 1 icon wide; remaining icons stack below
    RIGHT_COLLAPSED_W = 40   # one icon wide, matching the left sidebar

    def _build_left_rail(self):
        rail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        rail.get_style_context().add_class("studio-rail")
        rail.set_margin_start(8); rail.set_margin_end(8)
        rail.set_margin_top(8); rail.set_margin_bottom(8)
        # explicit False: buttons inside have hexpand, and GTK4 propagates
        # descendant expand to the pane unless pinned (r047)
        rail.set_hexpand(False)
        self._left_rail = rail
        self._left_collapsed = False
        self._fill_left()
        return rail

    def _toggle_left(self):
        self._left_collapsed = not self._left_collapsed
        self._clear(self._left_rail)
        self._fill_left()

    def _fill_left(self):
        rail = self._left_rail
        if self._left_collapsed:
            rail.set_size_request(self.LEFT_COLLAPSED_W, -1)
            expand = _icon_button("caret-right", "Expand", 16,
                                  css=("icon-24",), color=C["text_muted"])
            expand.connect("clicked", lambda *_: self._toggle_left())
            rail.append(expand)
            # consolidated profiles: hover pops out all six
            self._profile_buttons = {}
            profile_fly = []
            for name, (icon, meta) in PROFILE_META.items():
                b = _icon_button(icon, PROFILE_SHORT[name], 16,
                                 css=("icon-24", "pirow"))
                b.connect("clicked", lambda _b, n=name: self._profile(n))
                self._profile_buttons[name] = b
                profile_fly.append(b)
            self._mark_active_profile()
            rail.append(_flyout_button("camera", "Profiles", profile_fly))
            # consolidated tool groups: one anchor per function, hover = tools
            self._tool_buttons = {}
            for group, tools in TOOL_GROUPS:
                group_fly = []
                for name, icon in tools:
                    b = _icon_button(icon, name, 16,
                                     css=("icon-24", "toolcell"))
                    b.connect("clicked", lambda _b, n=name: self._pick_tool(n))
                    self._tool_buttons[name] = b
                    group_fly.append(b)
                rail.append(_flyout_button(GROUP_ICONS[group], group, group_fly))
            self._mark_active_tool()
            rail.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
            actions = self._action_buttons()
            for key in ("discard", "flatten", "captures", "copy", "save"):
                rail.append(actions[key])
            return

        rail.set_size_request(self.LEFT_W, -1)
        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        collapse = _icon_button("caret-left", "Collapse", 16,
                                css=("icon-24",), color=C["text_muted"])
        collapse.connect("clicked", lambda *_: self._toggle_left())
        head.append(collapse)
        rail.append(head)

        self._profile_buttons = {}
        pgrid = Gtk.Grid(row_spacing=4, column_spacing=4)  # 3 across fills 100
        for pi, (name, (icon, meta)) in enumerate(PROFILE_META.items()):
            b = _icon_button(icon, PROFILE_SHORT[name], 16,
                             css=("icon-24", "pirow"))
            b.set_hexpand(True)  # cells stretch so 3 columns fill the pane
            b.connect("clicked", lambda _b, n=name: self._profile(n))
            self._profile_buttons[name] = b
            pgrid.attach(b, pi % 3, pi // 3, 1, 1)
        rail.append(pgrid)
        self._mark_active_profile()

        # dense: grouped 24px cells fill the pane width (r057: no captions)
        self._tool_buttons = {}
        for gi_, (group, tools) in enumerate(TOOL_GROUPS):
            if gi_ > 0:
                rail.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
            grid = Gtk.Grid(row_spacing=4, column_spacing=4)
            for ti, (name, icon) in enumerate(tools):
                b = _icon_button(icon, name, 16,
                                 css=("icon-24", "toolcell"))
                b.set_hexpand(True)  # 3 columns fill the 100px pane
                b.connect("clicked", lambda _b, n=name: self._pick_tool(n))
                self._tool_buttons[name] = b
                grid.attach(b, ti % 3, ti // 3, 1, 1)
            rail.append(grid)
        self._mark_active_tool()

        spacer = Gtk.Box()
        spacer.set_vexpand(True)  # pins the actions to the lower left
        rail.append(spacer)
        rail.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        actions = self._action_buttons()
        grid = Gtk.Grid(row_spacing=4, column_spacing=4)
        for i, key in enumerate(("discard", "flatten", "captures",
                                 "copy", "save")):
            b = actions[key]
            b.set_hexpand(True)
            grid.attach(b, i % 3, i // 3, 1, 1)
        rail.append(grid)

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
                b.set_child(_icon_image(TOOL_NAMES[name], 16, C["on_accent"]))
                ctx.add_class("active")
            else:
                b.set_child(_icon_image(TOOL_NAMES[name], 16))

    def _pick_tool(self, name: str):
        self._active_tool = name
        self._mark_active_tool()
        self._refresh_options_bar()

    # --- center (s044 optbar + canvaswrap + zoomhud) ------------------------------

    def _build_center(self):
        center = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        center.set_hexpand(True); center.set_vexpand(True)

        self._options_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._options_bar.get_style_context().add_class("studio-options")
        # equal margins around the bar (r052)
        self._options_bar.set_margin_start(8); self._options_bar.set_margin_end(8)
        self._options_bar.set_margin_top(8); self._options_bar.set_margin_bottom(8)
        # horizontal scroll keeps the options bar's minimum width small, so
        # the window itself can shrink (r043); the bar scrolls when narrow
        opt_scroll = Gtk.ScrolledWindow()
        opt_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        opt_scroll.set_propagate_natural_height(True)
        opt_scroll.set_child(self._options_bar)
        center.append(opt_scroll)
        self._refresh_options_bar()

        overlay = Gtk.Overlay()
        overlay.set_vexpand(True)
        canvas = Gtk.DrawingArea()
        canvas.set_hexpand(True); canvas.set_vexpand(True)
        canvas.set_draw_func(self._draw_canvas)
        self._canvas = canvas
        scroll = Gtk.EventControllerScroll.new(
            Gtk.EventControllerScrollFlags.BOTH_AXES
            | Gtk.EventControllerScrollFlags.DISCRETE)
        scroll.connect("scroll", self._canvas_scroll)
        canvas.add_controller(scroll)
        overlay.set_child(canvas)

        hud = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        hud.get_style_context().add_class("zoomhud")
        self._hud_pct = Gtk.Label()
        self._hud_pct.get_style_context().add_class("zv")
        self._hud_pct.set_markup("<b>100%</b>")
        hud.append(self._hud_pct)
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
        bar.append(_icon_image(TOOL_NAMES.get(name, "cursor"), 16))
        label = Gtk.Label(label=name)
        label.get_style_context().add_class("lt-strong")
        bar.append(label)

        if name in ("Arrow", "Line", "Pen", "Marker"):
            bar.append(self._segment(("Thin", "Body", "Chunky"), 0,
                                     f"{name} stroke weight"))
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
        if name in ("Arrow", "Line", "Box", "Circle", "Text", "Pen", "Step",
                    "Callout", "Fill", "Marker"):
            spacer = Gtk.Box()
            spacer.set_hexpand(True)
            bar.append(spacer)
            sw = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            sw.get_style_context().add_class("swrow")
            for i, hexc in enumerate(CONTENT_COLORS):
                b = _hex_button(hexc, f"Content color {hexc}", "sw", 18)
                if i == 0:
                    b.get_style_context().add_class("sel")
                sw.append(b)
            bar.append(sw)  # right-aligned (r052)
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
        # standard stage background (r055: #242424, no checkerboard)
        cr.set_source_rgb(0x24 / 255, 0x24 / 255, 0x24 / 255)
        cr.paint()
        if self._capture is None:
            return
        pw, ph = self._capture.get_width(), self._capture.get_height()
        if pw <= 0 or ph <= 0:
            return
        scale = self._zoom  # original size unless ctrl+scroll zoomed (r057)
        dw, dh = pw * scale, ph * scale
        cr.save()
        cr.translate((w - dw) / 2, (h - dh) / 2)
        cr.scale(scale, scale)
        cr.rectangle(0, 0, pw, ph)
        cr.clip()
        Gdk.cairo_set_source_pixbuf(cr, self._capture, 0, 0)
        cr.paint()
        cr.restore()

    def _canvas_scroll(self, controller, dx, dy):
        """Ctrl + mouse wheel zooms the stage image (r057)."""
        if not (controller.get_current_event_state() & Gdk.ModifierType.CONTROL_MASK):
            return False
        delta = dy or dx
        self._set_zoom(self._zoom * (1.1 ** -delta))
        return True

    def _set_zoom(self, zoom: float):
        self._zoom = max(0.1, min(8.0, zoom))
        pct = f"{round(self._zoom * 100)}%"
        self._zoom_val.set_text(pct)
        self._hud_pct.set_markup(f"<b>{pct}</b>")
        self._canvas.queue_draw()

    # --- right panels (r044: 216px like the left, collapsible to 100px) ---------

    # --- right sidebar (r053: rebuilt on the left-sidebar model) ---------------
    # 100px expanded / 40px collapsed, caret toggle, captioned icon sections,
    # hover flyouts for panel content. Fixed pixels, never percentage.

    def _build_right_panels(self):
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        right.get_style_context().add_class("studio-panels")
        right.set_margin_start(8); right.set_margin_end(8)
        right.set_margin_top(8); right.set_margin_bottom(8)
        # explicit False: inner buttons expand, the pane must not (r047)
        right.set_hexpand(False)
        self._right_pane = right
        self._right_collapsed = False
        self._fill_right()
        return right

    def _toggle_right(self):
        self._right_collapsed = not self._right_collapsed
        self._clear(self._right_pane)
        self._fill_right()

    def _panel_content(self, name: str) -> Gtk.Box:
        """The flyout content for a panel (r053: panels live in flyouts)."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        if name == "Layers":
            box.append(self._build_layers_page())
        else:
            text = {
                "Captures": ("Captures - versions of this image. The list "
                             "lands with the panels milestone; the catalog "
                             "is read-only per D2."),
                "Props": ("Props - per-tool settings (colour, width, shadow, "
                          "usage note) land with the options-bar milestone."),
            }[name]
            l = Gtk.Label(label=text, wrap=True, xalign=0)
            l.set_max_width_chars(24)
            l.get_style_context().add_class("muted")
            box.append(l)
        return box

    def _fill_right(self):
        right = self._right_pane
        if self._right_collapsed:
            right.set_size_request(self.LEFT_COLLAPSED_W, -1)
            expand = _icon_button("caret-left", "Expand", 16,
                                  css=("icon-24",), color=C["text_muted"])
            expand.connect("clicked", lambda *_: self._toggle_right())
            right.append(expand)
            # consolidated: panels anchor (hover pops the three panels)
            panel_fly = []
            for name, (icon, _page) in PANEL_PAGES.items():
                content = self._panel_content(name)
                content.set_margin_start(4); content.set_margin_end(4)
                panel_fly.append(_flyout_box(icon, name, content))
            right.append(_flyout_button("stack", "Panels", panel_fly))
            # consolidated colour: palette flyout + screen eyedropper
            colour_fly = []
            for hexc in CONTENT_COLORS:
                b = _hex_button(hexc, hexc, "swp", 18)
                b.connect("clicked", lambda _b, h=hexc: self._set_fg(h))
                colour_fly.append(b)
            pick_btn = _icon_button("eyedropper", "Eyedropper", 16)
            pick_btn.connect("clicked", lambda *_: self._pick_colour())
            colour_fly.append(pick_btn)
            right.append(_flyout_button("palette", "Colour", colour_fly))
            return

        right.set_size_request(self.RIGHT_W, -1)
        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        collapse = _icon_button("caret-right", "Collapse", 16,
                                css=("icon-24",), color=C["text_muted"])
        collapse.connect("clicked", lambda *_: self._toggle_right())
        head.append(collapse)
        right.append(head)

        # panels: three icon tools, each a hover flyout with its content
        panels = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for name, (icon, _page) in PANEL_PAGES.items():
            content = self._panel_content(name)
            content.set_margin_start(4); content.set_margin_end(4)
            b = _flyout_box(icon, name, content)
            panels.append(b)
        right.append(panels)

        right.append(self._build_colour_card())

        spacer = Gtk.Box()
        spacer.set_vexpand(True)  # pins the navigator to the bottom
        right.append(spacer)
        right.append(self._build_minimap())

    def _build_minimap(self):
        wrap = Gtk.Box()
        wrap.get_style_context().add_class("mini")
        mini = Gtk.DrawingArea()
        mini.set_content_height(64)
        mini.set_hexpand(True)
        mini.set_draw_func(self._draw_minimap)
        wrap.set_margin_start(4); wrap.set_margin_end(4)
        wrap.set_margin_bottom(4)
        wrap.append(mini)
        return wrap

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
            empty.set_max_width_chars(12)
            empty.get_style_context().add_class("muted")
            empty.set_margin_top(8); empty.set_margin_start(8); empty.set_margin_end(8)
            self._layers_box.append(empty)
            return
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
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
        eye = _icon_button("eye", "Visibility", 16, css=("icon-24",))
        eye.set_sensitive(False)  # visibility toggles land with the object model
        row.append(eye)
        self._layers_box.append(row)

    # --- colour picker (r051: swatches/precise card, right pane) ----------------

    def _build_colour_card(self):
        """Reference restructure: swatches/precise tabs, current-colour
        circle, eyedropper, hex entry - fitted to the 100px pane."""
        self._fg = CONTENT_COLORS[0]
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        tabs = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self._sw_tab = _icon_button("grid-four", "Swatches", 16, css=("icon-24", "ptab"))
        self._pr_tab = _icon_button("sliders-horizontal", "Precise", 16,
                                    css=("icon-24", "ptab"))
        for b in (self._sw_tab, self._pr_tab):
            b.set_hexpand(True)
            tabs.append(b)
        self._sw_tab.connect("clicked", lambda *_: self._colour_page("swatches"))
        self._pr_tab.connect("clicked", lambda *_: self._colour_page("precise"))
        card.append(tabs)

        self._colour_stack = Gtk.Stack()
        self._colour_stack.set_transition_type(Gtk.StackTransitionType.NONE)
        grid = Gtk.Grid(row_spacing=2, column_spacing=2)
        self._palette_buttons: dict[str, Gtk.Button] = {}
        for i, hexc in enumerate(CONTENT_COLORS):
            b = _hex_button(hexc, f"{hexc}", "swp", 18)
            b.set_hexpand(True)
            b.connect("clicked", lambda _b, h=hexc: self._set_fg(h))
            self._palette_buttons[hexc] = b
            grid.attach(b, i % 4, i // 4, 1, 1)
        self._colour_stack.add_named(grid, "swatches")
        entry = Gtk.Entry()
        entry.get_style_context().add_class("hexentry")
        entry.set_tooltip_text("Hex")
        entry.set_max_width_chars(8)
        entry.connect("activate", lambda e: self._set_fg(e.get_text()))
        self._hex_entry = entry
        self._colour_stack.add_named(entry, "precise")
        card.append(self._colour_stack)

        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        circle = Gtk.Button()
        circle.get_style_context().add_class("fgcircle")
        area = Gtk.DrawingArea()
        area.set_content_width(12)
        area.set_content_height(12)
        self._fg_area = area
        area.set_draw_func(self._draw_fg_circle)
        circle.set_child(area)
        circle.set_tooltip_text("Foreground")
        bottom.append(circle)
        pick = _icon_button("eyedropper", "Eyedropper", 16)
        pick.connect("clicked", lambda *_: self._pick_colour())
        bottom.append(pick)
        card.append(bottom)

        self._colour_page("swatches")
        return card

    def _colour_page(self, page: str):
        self._colour_stack.set_visible_child_name(page)
        for tab, name in ((self._sw_tab, "swatches"), (self._pr_tab, "precise")):
            ctx = tab.get_style_context()
            ctx.remove_class("sel")
            if name == page:
                ctx.add_class("sel")

    def _draw_fg_circle(self, _area, cr, _w, _h):
        cr.set_source_rgba(*_hex_rgb(self._fg))
        cr.paint()

    def _set_fg(self, text: str):
        rgb = _parse_hex(text)
        if rgb is None:
            self._set_chip("cant", f"Not a hex colour: {text}")
            return
        self._fg = _to_hex(rgb)
        self._fg_area.queue_draw()
        for hexc, b in self._palette_buttons.items():
            ctx = b.get_style_context()
            ctx.remove_class("sel")
            if hexc.lower() == self._fg:
                ctx.add_class("sel")
        text_now = _to_hex(rgb)
        if self._hex_entry.get_text().lstrip("#").lower() != text_now[1:]:
            self._hex_entry.set_text(text_now)

    def _pick_colour(self):
        """Eyedropper: one-shot root grab + pixel read at the pointer."""
        if not capture.display_is_x11():
            self._set_chip("cant", "Colour picking needs X11")
            return
        frame = capture.grab_root()
        if frame is None:
            self._set_chip("cant", "Colour pick failed - could not grab the screen")
            return
        try:
            dev = self.get_display().get_default_seat().get_pointer()
            surface, sx, sy = dev.get_surface_at_position()
            if surface is None:
                raise ValueError("no surface under the pointer")
            rx, ry = surface.get_root_coords(sx, sy)
            pix = capture.crop(frame, Rect(rx, ry, 1, 1))
            if pix is None:
                raise ValueError("pixel outside the grabbed frame")
            px = pix.get_pixels()
            self._set_fg("#%02x%02x%02x" % (px[0], px[1], px[2]))
            self._set_chip("captured", f"Picked {self._fg}")
        except Exception as exc:  # pointer/coords quirks must not crash the app
            self._set_chip("cant", f"Colour pick failed: {exc}")

    def _build_panel_footer(self):
        """s044 pfoot, r043: colour well moved to the right pane, then
        quick styles, steps next-No, navigator minimap."""
        foot = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        foot.set_margin_top(4); foot.set_margin_bottom(4)

        colour_label = Gtk.Label(label="COLOUR", halign=Gtk.Align.START, xalign=0)
        colour_label.get_style_context().add_class("sect")
        colour_label.get_style_context().add_class("muted")
        foot.append(colour_label)
        foot.append(self._build_colour_card())

        qs_label = Gtk.Label(label="QUICK STYLES", halign=Gtk.Align.START, xalign=0)
        qs_label.get_style_context().add_class("sect"); qs_label.get_style_context().add_class("muted")
        foot.append(qs_label)
        qs = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for name, hexc in QUICK_STYLES:
            qs.append(_hex_button(hexc, name, "qs-sw", 24))
        foot.append(qs)


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
        cr.set_source_rgb(0x24 / 255, 0x24 / 255, 0x24 / 255)
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
        l.set_max_width_chars(12)  # caps NATURAL width (width_chars only raised minimum)
        l.set_margin_start(8); l.set_margin_end(8); l.set_margin_top(8)
        return l

    # --- action bar (s044 ab: Discard · Flatten · Captures-menu · summary ·
    #     Copy · Save; the status lives in the header chip only) -------------------

    def _captures_menu_button(self) -> Gtk.MenuButton:
        captures = Gtk.MenuButton()
        captures.set_tooltip_text("Captures")
        captures.set_child(_icon_image("images", 16))
        ctx = captures.get_style_context()
        ctx.add_class("lt-icon-btn"); ctx.add_class("icon-btn"); ctx.add_class("icon-24")
        popover = Gtk.Popover()
        popover.get_style_context().add_class("hoverfly")
        pop_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        pop_box.set_margin_start(4); pop_box.set_margin_end(4)
        pop_box.set_margin_top(4); pop_box.set_margin_bottom(4)
        open_btn = Gtk.Button(label="Open captures folder")
        open_btn.connect("clicked", lambda *_: self._open_captures_folder())
        pop_box.append(open_btn)
        later = Gtk.Button(label="Re-open editable (phase 6)", sensitive=False)
        later.set_tooltip_text("Later")
        pop_box.append(later)
        popover.set_child(pop_box)
        captures.set_popover(popover)
        return captures

    def _action_buttons(self) -> dict[str, Gtk.Button]:
        """The former action bar's icons (r052: they live in the sidebar)."""
        discard = _icon_button(
            "trash", "Discard", 16,
            css=("icon-24", "icon-danger"), color=C["error"])
        discard.connect("clicked", lambda *_: self._discard())
        flatten = _icon_button("stack", "Flatten", 16)
        captures = self._captures_menu_button()
        copy = _icon_button("copy", "Copy", 16)
        copy.connect("clicked", lambda *_: self._copy_clipboard())
        save = _icon_button(
            "download-simple", "Save",
            16, css=("icon-24", "primary"), color=C["on_accent"])
        save.connect("clicked", lambda *_: self._save())
        return {"discard": discard, "flatten": flatten, "captures": captures,
                "copy": copy, "save": save}

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
        self._set_chip("captured", f"Saved {self._saved_path.name}")
