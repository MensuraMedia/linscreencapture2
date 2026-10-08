# Pending

- Options bar (per-tool controls) + Layers/Captures/Props panels - next
  milestone per the ledger plan after the capture pipeline (r035 landed).
- Window snapping in the overlay: port v1 phase-3 window_geometry
  (XQueryTree hit-test via ctypes) so click-on-window captures it; the
  Window profile is inert until then.
- Wayland portal capture path (X11-only today; display_is_x11 guards).
- Zoom model on the canvas (percent / Fit), Navigator minimap.
- PrintScreen global hotkey + hidden-instance relaunch semantics (v1
  keybinding manager port).
- Consider a v2-side capture catalog: library.db stays read-only (D2
  forbids writing v1 files); save currently only writes the PNG.
- Settings capture_delay honored by Region; add a Delay stepper in Props
  later (spec: options bar numerics).

