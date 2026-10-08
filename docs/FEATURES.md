# LinScreenCapture 2 — Feature Documentation

What the application does today, as built through **r062** (2026-10-08).
Behaviour laws live in `AGENTS.md` (project rules 1–9); the design corpus
and authority order live in `docs/HANDOFF.md` §2a. Run with
`python3 -m linscreencapture2` (X11 required for capture).

## Capture (v1 freeze-frame pipeline, ported)

- **Profiles**: Region, Full screen, and Delayed 3 s are live (sidebar,
  first three profile icons). The studio window hides itself ~250 ms
  before the grab so it never appears in the frame; the whole root is
  snapshotted in one pass (ctypes libX11, `core/capture.py`), so menus
  and popups are frozen exactly as they were.
- **Region select**: after the freeze, drag on the frozen frame to select
  (dim outside, dashed border, live W×H chip, red crosshair). Esc
  cancels; Enter accepts; drag ≥ 5px, otherwise treated as a cancel.
  Return/Enter accepts the current selection.
- **Full screen**: grabs the entire root without the overlay.
- **Delayed 3 s**: arms the region capture after a 3-second delay.
- **Window / Scrolling / Pin** are queued (status bar explains); they
  land with the window-geometry port and later phases.
- **Save**: writes `LinCapture_YYYYmmdd_HHMMSS.png` into the v1 captures
  folder (collision-safe — never overwrites; a `-2` suffix is added).
- **Copy**: puts the capture on the clipboard as an image.
- **Discard**: drops the capture and returns the chip to Ready.

## Stage (canvas)

- Solid **#242424** background.
- Captures load at **original size**, centred — never auto-fitted.
- **Ctrl + mouse wheel** zooms (about 1.1× per notch, clamped 0.1×–8×);
  the percentage updates live in the canvas HUD chip and the header.
- The window is always exactly the size you set: if content does not
  fit, it scrolls — the window itself never grows (r061).

## Sidebars

Both sidebars are mirror images: **100px expanded / 40px collapsed**,
toggled with the caret in each pane's header, fixed pixels — never
percentages. All buttons are square, 24×24, with 10px ink-normalized
Phosphor glyphs (the only icon source is the vendored set at
`assets/icons/phosphor/regular`). Single-word hover captions on flat
#141414 tooltips.

- **Collapsed**: every button is present, stacked one per row — nothing
  is hidden behind flyouts and there is no scroller; overflow is reached
  by expanding the sidebar.
- **Left (capture)**: 6 capture profiles; the 19 tools grouped by
  function (Select, Draw, Redact, Content, Transform, Edit — rules only,
  no captions); ACTIONS pinned at the bottom when expanded (Discard,
  Flatten*, Captures menu, Copy, Save). *Flatten is queued (phase 15).
- **Right (panels)**: Layers / Captures / Props panel tools — Layers
  shows the live layer rows (the Base capture, with kind chip and
  visibility toggle placeholder); Captures and Props show their
  scheduled-phase notes. Below them the **colour picker**:
  Swatches/Precise tabs, the fixed 12-colour content palette with a
  selection ring, the current-colour square, a working **eyedropper**
  (picks any pixel on the screen), and a hex entry (3- or 6-digit).
- **Navigator**: a live minimap of the capture, pinned to the bottom of
  the expanded right sidebar.

## Header

- Document block: `Untitled` until saved (then the filename), with the
  `Edit · W×H · PNG · N layer(s) · state` sub-line — the capture summary
  lives here.
- State chip: **Ready / Selecting / Captured / Can't capture** with the
  reason on hover (contract vocabulary and colours).
- Zoom controls (Out / In / Fit) and the 24px Capture button. The zoom
  percentage is shared with the stage HUD.

## Action bar

Removed by directive (r052) — its icons live in the left sidebar's
ACTIONS section; the summary lives in the header sub-line.

## Capture-bar (overlay)

Queued as the next milestone (corner handles, top-centre size chip,
freeze chips, the Annotate/Copy/Save capture bar, end toast, 8×
magnifier) — see `docs/HANDOFF.md` §7 item 2.

## Known limits

- X11 only for capture (Wayland portal is queued).
- Window/Scrolling/Pin profiles, window snapping, annotation tools,
  options-bar behaviour, and the Keyboard settings table are queued —
  see `docs/HANDOFF.md` §7 for the full ordered list.
