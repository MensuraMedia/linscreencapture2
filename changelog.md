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

## 2026-10-07 - r037/r038 icon-button chrome + handoff docs

- UI law r037 (operator): every button is an icon button, labels only in
  hover tooltips; even padding/margins on a 4px grid. Applied across the
  shell: header (zoom group, camera Capture 24px primary), capture
  profiles 3x2 grid, tools 4-column grid, panel switcher, action bar
  (Discard red, Flatten, Captures, Copy, Save 24px primary). Labels live
  as tooltips; icon set per PROFILE_ICONS/TOOL_ICONS/PANEL_ICONS maps.
- ui/icons.py: app-side Phosphor loader over the full vendored
  assets/icons/phosphor/regular set (kit's curated 20-icon subset stays
  stock); currentColor mechanism identical to lintheme.icons.
- D10 fix: kit CSS loads at USER priority, so APP_CSS at APPLICATION
  priority lost ties - accent backgrounds on primary icon buttons never
  rendered. APP_CSS now installs at USER priority after apply.install,
  with a parsing-error reporter. Verified by rig render: accent chips
  render (chrome_r038).
- tools/rig.sh (up/down/status): mandatory rig teardown - the Xephyr
  window shows on the operator's desktop and must not linger (operator
  noticed it mid-session).
- docs/HANDOFF.md: comprehensive build handoff + QA reference (state,
  operator law, architecture, D1-D10, 4-gate verification protocol,
  pitfalls, work queue, bookkeeping, adversarial review checklist).
- AGENTS.md: stack filled in; project rules 1-4 recorded (r037 law,
  CSS priority, tools/ convention + teardown, freeze-frame invariant).
- Tests 13/13 (new test_icons: every referenced icon resolves, pixbuf
  sizes correct); compileall clean; rig render verified.

## 2026-10-07 - r041 documentation deep-dive + design-corpus correction

- Deep-dive across the whole design corpus: v2 spec, the s044 mockup DOM
  (exact formation order), DESIGN-CONTRACT.md r027 (25 checkable items,
  linshot3 read-only), s035 component sheet + s036 freeze overlay + s037
  gallery renders, GUI guide + docs/01-07. Finding: the r039 audit
  under-called deviations - profile ROWS, 2-col 40x40 tool grid, top
  panel tabs, size chip top-center + 4 corner handles are spec'd
  formation (r037 changes labels, not formation); the overlay's
  auto-confirm-on-release contradicts the documented capture bar
  (Annotate/Copy/Save + saves-as hint); stateful status chip vocabulary,
  freeze chips, end toast, magnifier, color well, min window 720x540 are
  all documented intent not yet built. Operator verdict confirmed: the
  current shell does not yet adequately represent the intended design.
- docs/HANDOFF.md: new section 2a (design corpus + authority order +
  r039 corrections), work queue rebuilt as F (formation pass, overlay
  contract items) vs B (behavior phases) with the full deviation list;
  pitfall added: live-desktop grabs are not evidence, rig only.
- No code changes this marker; correction plan queued for r042.

## 2026-10-08 - r042 formation pass: s044 mockup reproduced

- Operator directive: reproduce the mockup using the analyzed standards
  before any further build. The shell now matches s044 formation under
  the authority order (spec s2/s3 + DESIGN-CONTRACT items + r034/r037
  overrides):
  - header: doc block ("Untitled" / "LinCapture_….png" after save +
    "Edit · N layer(s) · unsaved changes|saved"), stateful chip with dot
    and contract #6 vocabulary (Ready/Selecting/Captured/Can't capture +
    ok/busy/attention colors, reason in tooltip), zoom control (radius 8
    container), 24px Capture primary.
  - left rail: 6 capture-profile ROWS (40px, active raised, meta in
    tooltip), TOOLS as 2-column 40x40 grids per contract #4 groups
    (Select | Draw | Redact | Content | Transform | Edit) with
    separators, active tool accent-filled with on-accent icon, color
    well (fg red / bg white over + swap) pinned to rail bottom.
  - options bar: per-tool formation (s044 optbar): tool identity,
    Thin/Body/Chunky + Square/Rounded segments (accent-selected),
    12-swatch contract-#9 content palette with selection ring, Shadow
    toggle, Head 1.0x / Body 16px / intensity / next-No numerics.
  - right column: tabs at TOP (accent underline, icon-only per r037),
    Layers page with lrow formation (thumb · Base capture · IMG · eye),
    placeholder Captures/Props, footer: quick styles (4 presets), steps
    next-No badge, navigator minimap (live thumbnail).
  - action bar: Discard(danger) · Flatten · Captures menu (caret popover:
    Open captures folder works; re-open editable disabled-with-reason) ·
    summary "W × H · PNG · N layer(s) · 100%" · Copy · Save; duplicate
    status label removed (status = header chip only).
  - window: title "LinScreenCapture - Studio Editor", min size 720x540
    (contract #14).
- GTK CSS lesson: no display:flex/gap/width - layout via widget
  properties, CSS paints only (rendered clean after rewrite).
- Capture pipeline untouched and re-verified in the rig render (real
  XTEST capture during the render). Tests 14/14 (content-palette test
  added); compileall clean. Evidence: docs/design/r042_formation_
  reproduction.png. PAUSED for operator review before further build
  (overlay contract items are next, HANDOFF 7.2).

## 2026-10-08 - r043 compact chrome: minimized buttons, swatch right, smaller window

- Operator directives: minimize buttons further; place swatch on the
  right pane; ensure window dimensions shrink smaller.
- Buttons: the 24px square is now the standard for ALL icon buttons
  (were 32px) - header zoom (14px glyphs), capture profiles (28px rows,
  16px glyphs), tool cells 24x24, action bar, layers eye, menu button,
  quick styles 20px. Primaries stay 24px (r034 floor).
- Colour well moved from the left rail to the right-pane footer:
  COLOUR section (fg red / bg white + swap) above QUICK STYLES.
- Window: default 1280x800 -> 960x640; options bar wrapped in a
  horizontal ScrolledWindow so its single row no longer forces the
  window minimum up (it scrolls when narrow). Desktop relaunch: 960
  wide, zero criticals. Note: natural content minimum keeps height
  around 790 until the panel stack scrolls (queued with panels work).
- Rig pitfall fixed (D11): a running desktop instance owns the DBus app
  id, so rig drivers silently no-op'd (activate never fired) - drivers
  now set Gio.ApplicationFlags.NON_UNIQUE.
- Tests 14/14; compileall clean.
