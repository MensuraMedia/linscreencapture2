# 2. GTK: how each mockup component is built

Every component of the 2026 redesign mockups maps to standard GTK widgets. Nothing needs a
custom toolkit, a web view or libadwaita.

## 2.1 Component map

| Mockup component | GTK 3 (lintheme/gtk3) | GTK 4 equivalent |
|---|---|---|
| Header bar with brand, crumb, status chip, menu | `Gtk.HeaderBar` (`set_titlebar`), `StatusChip(Gtk.Button)` | `Gtk.HeaderBar` (`set_titlebar`), same button |
| Navigation rail, active item | `NavRail`: `Gtk.Box` of `Gtk.Button`s, class `lt-active` | same with `append` |
| Count badge on a rail icon | `Gtk.Overlay` + `Gtk.Label.lt-badge` (no CSS positioning needed) | `Gtk.Overlay.add_overlay` |
| Pages | `Gtk.Stack` with crossfade (0 ms when animations are off) | `Gtk.Stack` |
| Card | `Card(Gtk.Box)` + CSS border, radius, padding | same |
| Segmented choice (2–4 options) | `Gtk.RadioButton` with `set_mode(False)` in a linked box: radio semantics, arrow keys | `Gtk.ToggleButton.set_group` (or `Adw.ToggleGroup` with libadwaita ≥ 1.7) |
| Stepper (copies, zoom, %) | `Stepper`: − label + buttons, ends disabled at limits | same |
| Dropdown (5+ options) | `Gtk.ComboBoxText` | `Gtk.DropDown` |
| Switch row | `Gtk.Switch` named after its title | same |
| Page-range entry, invalid state | `Gtk.Entry` + `lt-invalid` + message label | same |
| Banner (ok / busy / attention / error) | `Banner(Gtk.Box)` with icon, markup, action buttons | same (or `Adw.Banner`, not used) |
| Ink / level gauge | `Gauge`: `Gtk.DrawingArea` + Cairo (multi-colour stripes, paper track, outline) | `Gtk.DrawingArea.set_draw_func` |
| Progress | `Gtk.ProgressBar` styled | same |
| Live preview with shaded margins | `Gtk.DrawingArea` + Cairo (apps draw their rendered pages) | `set_draw_func` or `Gtk.Picture` |
| Page thumbnails | `Gtk.Button.lt-thumb` (`lt-active` ring) | same |
| Sticky action bar (summary · busy · done) | `ActionBar`: `Gtk.Stack` of three states + right-hand actions | same |
| Status hero | `Hero(Gtk.Box)` | same |
| Guided troubleshooter steps | `StepLadder(Gtk.Box)` with named steps | same |
| Empty state | `EmptyState(Gtk.Box)` | same (or `Adw.StatusPage`) |
| Confirm dialog | `confirm()`: `Gtk.Dialog.run()`, verbs on buttons, Esc cancels | `Gtk.AlertDialog` (async; no `run()`) |
| Keyboard shortcuts | `key-press-event` in `DashboardWindow` (Alt+1…9) | `Gtk.ShortcutController` |
| Narrow window (< 960 px) | `size-allocate` → `on_layout('compact')` | `Adw.Breakpoint` or `notify::default-width` |

## 2.2 Pitfalls found while building the kit (GTK 3)

1. **`set_hexpand(True)` propagates upwards.** An icon set to expand inside a 44 px tile made the
   whole options column and the action bar's left side expand. Centre with `set_halign/valign`
   and `pack_start(..., True, True, 0)` instead; use `hexpand` only on spacers and real columns.
2. **`Gtk.Stack` ignores `set_visible_child_name` for a hidden child.** Setting the action bar to
   "done" before `show_all()` silently showed the empty "idle" state. Components `show_all()` their
   stack children at construction.
3. **The system theme fights back.** Mint-Y draws gradients, text shadows and its own switch;
   the CSS clears `background-image` and `text-shadow` and is installed at
   `STYLE_PROVIDER_PRIORITY_USER`.
4. **A broad `label { color: inherit }` rule beats status text classes** (`.lt-root label` is more
   specific than `.lt-attention-text`). Labels inherit colour anyway: no such rule.
5. **Fixed-size circles stretch.** A `min-height` label inside a taller box fills it; give it
   `valign CENTER`.
6. **A tall options column pushes the action bar off-screen.** Put it in `scrolled()`; the action
   bar stays outside the scroller.
7. **Black on dark is invisible.** Gauges draw on a light, paper-like track so black ink reads.
8. **Window controls inherit low contrast.** `.lt-header button.titlebutton` is styled explicitly.

## 2.3 Threading and responsiveness

Status checks, rendering and device I/O run in worker threads; widgets change only on the main
loop through `GLib.idle_add`. Acknowledge every click within ~100 ms (a spinner or a state change);
anything longer than 1 s says what it is doing. Never block the main loop for a device.

## 2.4 Testing

- `xvfb-run -a python3 -m pytest -q`: tokens, CSS parsing in GTK 3 and GTK 4 (each in its own
  process: the two can't share one), component behaviour and accessible names.
- `bash tools/screenshots.sh`: every page and state rendered headlessly into `docs/images/`.
- Look at the screenshots: four of the eight pitfalls above were only visible there.
