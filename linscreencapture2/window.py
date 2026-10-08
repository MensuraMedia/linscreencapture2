"""StudioWindow - the Studio Editor shell (GTK4).

Regions per docs/design/STUDIO-EDITOR-SPEC.md section 3: header, options
bar, left rail (capture profiles + tools + color well), canvas, right
panel stack (Layers / Captures / Props), action bar. Theming via the
vendored lintheme kit (apply.install), GTK4."""
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from lintheme import apply

from linscreencapture2.core.settings import Settings
from linscreencapture2.core import library

APP_CSS = b"""
.root .studio-header { border-bottom: 1px solid var(--border); }
/* r034 shape language: rounded squares only - no pills */
.studio-header .chip { border-radius: 6px; padding: 4px 10px; }
.zoom { border-radius: 8px; }
"""


class StudioWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("LinScreenCapture")
        self.set_default_size(1280, 800)
        apply.install(self)
        provider = Gtk.CssProvider()
        provider.load_from_data(APP_CSS)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.get_style_context().add_class("studio-root")

        self.settings = Settings.load()
        self._build()

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
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bar.get_style_context().add_class("studio-header")
        bar.set_margin_start(16); bar.set_margin_end(16)
        bar.set_margin_top(8); bar.set_margin_bottom(8)

        title = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        t = Gtk.Label(label="LinScreenCapture", halign=Gtk.Align.START)
        t.get_style_context().add_class("title")
        s = Gtk.Label(label="Edit - unsaved changes", halign=Gtk.Align.START)
        s.get_style_context().add_class("muted")
        title.append(t); title.append(s)
        bar.append(title)

        chip = Gtk.Label(label="Ready")
        chip.get_style_context().add_class("chip")
        bar.append(chip)

        spacer = Gtk.Box(); bar.append(spacer); spacer.set_hexpand(True)

        zoom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        zoom.get_style_context().add_class("zoom")
        for label in ("-", "100%", "+", "Fit"):
            zoom.append(Gtk.Button(label=label))
        bar.append(zoom)

        cap = Gtk.Button(label="Capture")
        cap.get_style_context().add_class("capture")
        cap.set_tooltip_text("Freeze the screen and select a region (PrintScreen)")
        cap.connect("clicked", lambda *_: self._capture_stub())
        bar.append(cap)
        return bar

    def _capture_stub(self):
        # Phase: port the v1 freeze-frame pipeline (GTK3 -> GTK4).
        self.set_status("Capture pipeline port is scheduled")

    def set_status(self, text: str):
        self._status.set_text(text)

    def _build_left_rail(self):
        rail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        rail.get_style_context().add_class("nav-rail")
        rail.set_size_request(216, -1)
        rail.set_margin_top(8); rail.set_margin_bottom(8)

        cap = Gtk.Label(label="CAPTURE PROFILES", halign=Gtk.Align.START)
        cap.get_style_context().add_class("sect"); cap.get_style_context().add_class("muted")
        rail.append(cap)
        for name in ("Region", "Window", "Full screen", "Scrolling", "Delayed 3 s", "Pin to screen"):
            b = Gtk.Button(label=name); b.set_halign(Gtk.Align.FILL)
            b.get_style_context().add_class("nav-row")
            rail.append(b)

        tools = Gtk.Label(label="TOOLS", halign=Gtk.Align.START)
        tools.get_style_context().add_class("sect"); tools.get_style_context().add_class("muted")
        rail.append(tools)
        grid = Gtk.FlowBox(); grid.set_min_children_per_line(2); grid.set_max_children_per_line(2)
        grid.set_column_spacing(4); grid.set_row_spacing(4)
        for name in ("Select", "Move", "Line", "Arrow", "Box", "Circle", "Text", "Pen",
                     "Marker", "Blur", "Pixelate", "Step", "Callout", "Fill",
                     "Crop", "Resize", "Rotate", "Bright", "Dupe"):
            b = Gtk.Button(label=name)
            grid.append(b)
        rail.append(grid)
        return rail

    def _build_center(self):
        center = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        center.set_hexpand(True); center.set_vexpand(True)

        opts = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        opts.get_style_context().add_class("options-bar")
        opts.append(Gtk.Label(label="Arrow (options bar - content per active tool)"))
        center.append(opts)

        canvas = Gtk.DrawingArea()
        canvas.set_hexpand(True); canvas.set_vexpand(True)
        canvas.set_draw_func(self._draw_canvas)
        center.append(canvas)
        return center

    def _draw_canvas(self, area, cr, w, h):
        # checkerboard placeholder until the capture pipeline lands
        cr.set_source_rgb(0.102, 0.122, 0.145)
        cr.paint()
        cr.set_source_rgb(0.149, 0.165, 0.188)
        step = 16
        for y in range(0, h, step):
            for x in range(0, w, step * 2):
                cr.rectangle(x + (y // step % 2) * step, y, step, step)
        cr.fill()

    def _build_right_panels(self):
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        right.get_style_context().add_class("panels")
        right.set_size_request(280, -1)

        stack = Gtk.Stack(); stack.set_vexpand(True)
        stack.add_named(self._page_label("Layers - annotation object model (phase 12/15)"), "layers")
        stack.add_named(self._page_label("Captures - versions of this image (library, phase 6)"), "captures")
        stack.add_named(self._page_label("Props - active tool settings"), "props")
        right.append(stack)

        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        for name, page in (("Layers", "layers"), ("Captures", "captures"), ("Props", "props")):
            b = Gtk.Button(label=name); b.set_hexpand(True)
            b.connect("clicked", lambda _b, p=page: stack.set_visible_child_name(p))
            bar.append(b)
        right.append(bar)
        return right

    def _page_label(self, text):
        l = Gtk.Label(label=text); l.set_wrap(True)
        l.set_margin_start(12); l.set_margin_end(12); l.set_margin_top(12)
        return l

    def _build_action_bar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.get_style_context().add_class("action-bar")
        bar.set_margin_start(16); bar.set_margin_end(16)
        bar.set_margin_top(6); bar.set_margin_bottom(6)

        for name in ("Discard", "Flatten", "Captures"):
            bar.append(Gtk.Button(label=name))
        spacer = Gtk.Box(); bar.append(spacer); spacer.set_hexpand(True)
        summary = Gtk.Label(label="no capture")
        summary.get_style_context().add_class("muted")
        bar.append(summary)
        bar.append(Gtk.Button(label="Copy"))
        save = Gtk.Button(label="Save")
        save.get_style_context().add_class("capture")
        bar.append(save)

        self._status = Gtk.Label(label="Ready")
        self._status.get_style_context().add_class("muted")
        bar.append(self._status)
        return bar
