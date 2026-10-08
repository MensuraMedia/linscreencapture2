# Changelog — LinScreenCapture 2

Append-only. Newest entries at the bottom. One entry per completed change.

## 2026-10-07
- Project bootstrapped with development standards (s003).

## 2026-10-07 - r034 scaffold: GTK4/Python Studio Editor

- Bootstrap per linapptemplate conventions: lintheme vendored (kit),
  app package linscreencapture2 (app.py, window.py = StudioWindow GTK4
  shell: header/options bar/capture profiles/tools grid/canvas/
  Layers-Captures-Props stack/action bar), core (paths/settings/library
  with v1 import-in-place per D2), tests 4/4 display-free.
- Studio spec + mockup renders + adopting docs copied into docs/.
- Pushed: initial scaffold commit + render (origin/main).
- Known: 1 accessibility-bus CRITICAL at startup (at-spi in the rig;
  harmless, standard GTK warning) - fix with NO_AT_BRIDGE in dev launcher.
- r034 directives applied to the design: no pills, hover-only shortcuts,
  Captures naming, 24px primaries (mockups + spec; app CSS follows).

## 2026-10-07 - r035 capture pipeline: v1 freeze-frame ported to GTK4

- core/capture.py: whole-root grab via ctypes libX11 (XGetImage on the
  root, XWindowAttributes for exact dims) - GTK4 removed
  Gdk.pixbuf_get_from_window/Gdk.Screen, so v1 screen_capture.c semantics
  are ported directly; C-speed slice conversion for standard LE/BGRX with
  numpy generic fallback. Rect math (normalize/clamp/too-small) pure and
  unit-tested; v1 naming LinCapture_YYYYmmdd_HHMMSS.png with collision
  suffix; save_png never overwrites in the shared captures folder.
- ui/capture_overlay.py: FreezeOverlay - one undecorated fullscreen
  window per monitor over the pre-grabbed frozen frame (freeze-frame
  invariant kept: frame exists before any overlay window). Drag>=5px
  selects (dim outside, dashed border, WxH chip, red crosshair),
  click/tiny drag and Esc cancel, Return accepts. GTK4 deltas from v1:
  monitors via ListModel, WM hints gone (skip-taskbar/keep-above removed
  upstream), GestureDrag offsets replace raw motion events.
- window.py: Region/Full screen/Delayed 3 s profiles + header Capture
  wired; Window/Scrolling/Pin report their scheduled phase. Studio hides
  (250ms settle) before freezing so it never lands in the frame. Capture
  loads as canvas Base layer (fitted draw over the checker page); Copy
  (clipboard texture), Save (shared folder, D2), Discard live. Status/
  summary/doc-sub update per spec wording. APP_CSS var() bug fixed (GTK
  4.14 has no CSS var(); lintheme substitutes tokens in Python).
- app.py: NO_AT_BRIDGE=1 before Gtk import - the rig at-spi CRITICAL is
  gone (0 criticals in the rig log now).
- Rig verified end-to-end (tools/rig_capture_smoke.py, Xephyr :61 +
  muffin, XTEST-driven drag): freeze -> 640x480 crop at exact coords ->
  gradient content pixel-verified -> Save PNG written. Renders:
  docs/design/r035_freeze_overlay_mid_drag.png (live selection with dim/
  border/chip), docs/v2_region_capture_on_canvas.png. Rig facts: muffin
  resizes the Xephyr root to host RandR modes (use relative drag
  geometry); GdkPixbuf crops keep the parent rowstride.
- Tests 11/11 display-free; compileall gate clean.
- Not in this pass: window snapping (needs the v1 phase-3 geometry
  port), Wayland portal capture, zoom model, options bar, panels.
