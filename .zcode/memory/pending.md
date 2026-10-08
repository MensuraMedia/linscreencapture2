# Pending

- Next milestone (ledger plan): options bar (per-tool controls), then
  Layers/Captures/Props panels. Reference: docs/HANDOFF.md section 7.
- Window snapping in the overlay: port v1 phase-3 window_geometry
  (XQueryTree hit-test via ctypes) so click-on-window captures it; the
  Window profile is inert until then.
- Wayland portal capture path (X11-only today; display_is_x11 guards).
- Zoom model on the canvas (percent / Fit), Navigator minimap.
- PrintScreen global hotkey + hidden-instance relaunch semantics (v1
  keybinding manager port).
- Consider a v2-side capture catalog: library.db stays read-only (D2
  forbid writes); save currently only writes the PNG.
- Settings capture_delay honored by Region; add a Delay stepper in Props
  later (spec: options bar numerics).
- RIG TEARDOWN IS MANDATORY: tools/rig.sh down when a render/verify
  session ends (operator saw the Xephyr window on their desktop, r038).

