# 1. Stack

Lin* apps are native Linux desktop utilities: **Python 3 + GTK through PyGObject**, styled by
**GTK CSS** generated from Python tokens, drawn with **Cairo** where widgets aren't enough
(previews, gauges). Everything comes from distribution packages and works offline.

## 1.1 Verified versions (Linux Mint 22.3, Ubuntu 24.04 "noble" base, 2026-10-02)

| Component | Package | Version | Used for |
|---|---|---|---|
| Python | `python3` | 3.12.3 | everything (code targets 3.10+) |
| PyGObject | `python3-gi` | 3.48.2 | GTK, GLib, GdkPixbuf, Pango bindings |
| GLib | (with PyGObject) | 2.80.0 | main loop; `GLib.idle_add` returns work to the GTK thread |
| Cairo bindings | `python3-gi-cairo`, `python3-cairo` | 3.48.2 / 1.25.1 | drawing areas (preview, gauges) |
| GTK 3 | `gir1.2-gtk-3.0`, `libgtk-3-0t64` | 3.24.41 | **the toolkit of every Lin* app today** |
| GTK 4 | `gir1.2-gtk-4.0`, `libgtk-4-1` | 4.14.5 | parity proven (examples/gtk4_parity.py); not adopted yet |
| libadwaita | `gir1.2-adw-1` | 1.5.0 | **not used**: it would restyle everything as Adwaita |
| SVG loader | `librsvg2-common` | 2.58.0 | renders the bundled Phosphor icons through GdkPixbuf |
| GdkPixbuf, Pango | `gir1.2-gdkpixbuf-2.0`, `gir1.2-pango-1.0` | 2.42.10 / 1.52.1 | icons, font check |
| Font | `fonts-ubuntu` | 0.869 | Ubuntu and Ubuntu Mono (shipped with Mint and Ubuntu) |
| Tests | `xvfb`, pytest | 21.1.12 / — | headless display for widget tests and screenshots |
| Lint | `black`, `python3-pyflakes` | 24.2.0 / 3.2.0 | line length 110 |

App-specific packages sit on top; LinPrinter's, for example:

| Component | Package | Version | Used for |
|---|---|---|---|
| Imaging | `python3-pil`, `ghostscript` | 10.2.0 / 10.02.1 | documents to PDF and PWG raster |
| Printing | `ipp-usb`, `cups` | 0.9.24 / 2.4.7 | IPP over USB; the system queue fallback |

Runtime packages an app built on lintheme needs (add them to the app's `app.json` → `offline`
and its installer, as LinPrinter does):

```
python3 python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-gdkpixbuf-2.0 gir1.2-pango-1.0 librsvg2-common fonts-ubuntu
```

Check a machine against this table (prints the versions that are actually loaded):

```bash
python3 - <<'PY'
import gi, platform
gi.require_version("Gtk", "3.0"); from gi.repository import Gtk, GLib
print("Python", platform.python_version(), "| PyGObject", gi.__version__,
      "| GLib %d.%d.%d" % (GLib.MAJOR_VERSION, GLib.MINOR_VERSION, GLib.MICRO_VERSION))
print("GTK 3 (used): %d.%d.%d" % (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version()))
PY
dpkg -l libgtk-3-0t64 gir1.2-gtk-3.0 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 | awk '/^ii/{print $2, $3}'
```

Last checked 2026-10-02 on Linux Mint 22.3: Python 3.12.3, PyGObject 3.48.2, GLib 2.80.0,
**GTK 3.24.41** (package 3.24.41-4ubuntu1.3) in use; GTK 4.14.5 and libadwaita 1.5.0 installed, unused.

## 1.2 GTK 3 now, GTK 4 ready

**Decision (2026-10-02): the kit's components target GTK 3.24; the theme layer targets both.**

- LinPrinter, LinScanner and LinFileCopy are GTK 3 apps, with GTK 3 tests, walkthroughs and
  packaging. Restyling them needs no port.
- Every mockup component was rendered in real GTK 3 *and* GTK 4 widgets with the same generated
  CSS (`docs/images/gtk4-parity.png`). Nothing in the design needs GTK 4.
- On Mint 22, GTK 4 is 4.14: no CSS custom properties (4.16+), and libadwaita 1.5 lacks
  `Adw.ToggleGroup` (1.7+). Neither blocks a port; both are reasons not to rush it.
- A later move to GTK 4 keeps `tokens`, `css` (`build_css(4)`), `apply`, `status` and `icons`
  unchanged and rewrites only `lintheme/gtk3` as `lintheme/gtk4` (mapping in [02-GTK.md](02-GTK.md)).

## 1.3 Rules inherited from the Lin* projects

- Distribution packages only, no pip at runtime; installs offline from the linux-peripherals pool.
- No network, no telemetry, no AI. USB devices only where devices are involved.
- Anything blocking runs off the GTK thread; results come back with `GLib.idle_add`.
- Copy, don't reference: an app vendors `lintheme/` into its own tree (see [06-ADOPTING.md](06-ADOPTING.md)).
