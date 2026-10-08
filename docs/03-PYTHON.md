# 3. Python: package layout and conventions

## 3.1 The package

```
lintheme/
  __init__.py      version, THEME
  tokens.py        colours, type, space, size, layout, motion; contrast math    (no GTK)
  css.py           build_css(3 | 4) from tokens; CLASSES                         (no GTK)
  status.py        the four states, chip text, message pattern, message linter   (no GTK)
  icons.py         bundled Phosphor SVGs → GdkPixbuf in any colour               (GdkPixbuf only)
  apply.py         install the CSS in a running GTK 3 or 4 app
  icons/           20 Phosphor regular SVGs + LICENSE-phosphor (MIT)
  gtk3/
    components.py  every component (classes and factories)
    shell.py       DashboardWindow: header bar, status chip, rail, pages, shortcuts, layout modes
examples/          demo_app.py (a complete dashboard), gallery.py, gtk4_parity.py
tools/             screenshots.sh, contrast.py
tests/             pytest; GTK tests run under xvfb-run
```

Layers, lowest first: `tokens` ← `css`, `status`, `icons` ← `apply` ← `gtk3`. Nothing lower
imports anything higher, and only `gtk3` (and `apply`) import Gtk, so the first four modules work
with either toolkit and in plain unit tests.

## 3.2 Conventions

- Python 3.10+, standard library + PyGObject only. Black at 110 columns, pyflakes clean.
- Components are plain Gtk widgets (subclasses or factories); styling only through `lt-` classes;
  no inline colours. Apps add their own classes with their own prefix.
- Every interactive widget gets an accessible name (`components.name`), icon-only buttons a
  tooltip too. Tests assert the names.
- Docstrings say what a thing is for in one line; comments explain *why*, not what.
- In apps, keep the Lin* layering: pages → managers → backends; pages never talk to a device.

## 3.3 Using the components

```python
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from lintheme import status
from lintheme.gtk3 import components as ui
from lintheme.gtk3.shell import DashboardWindow

win = DashboardWindow(app, "LinScanner", "printer")
page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
card = ui.Card("Scanner", action=("Change", choose_scanner))
card.add_row(ui.item_row("printer", "Epson ES-400 II", ui.status_line("ok", "Ready · feeder loaded")))
page.pack_start(card, False, False, 0)
win.add_page("scan", "Scan", "upload-simple", page)
win.chip.set_status("Epson ES-400 II", "ok")
bar = ui.ActionBar()
bar.idle("Duplex · 300 dpi · PDF", "Feeder, both sides")
bar.add_action(ui.with_shortcut(ui.button("Scan", kind="primary", big=True), "Ctrl+S"))
```

Messages follow the pattern in `status.message(what, why, next_step)`; `status.problems(text)`
flags urgency words, raw error codes and shouting, so a test can lint an app's strings.
