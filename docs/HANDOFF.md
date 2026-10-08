# LinScreenCapture 2 — Build Handoff & QA Reference

Single entry point for (a) a fresh agent session continuing this project and
(b) an adversarial reviewer auditing build quality. Read top to bottom;
everything here is verified state as of **r038 (2026-10-07)**. Sections:
[state](#1-state-summary) · [law](#2-operator-law-normative) ·
[architecture](#3-architecture) · [decisions](#4-decision-register) ·
[QA protocol](#5-verification--qa-protocol) · [pitfalls](#6-known-pitfalls) ·
[work queue](#7-work-queue) · [bookkeeping](#8-bookkeeping-conventions) ·
[review checklist](#9-adversarial-review-checklist).

## 1. State summary

GTK4/Python Studio Editor (Photoshop × Snagit hybrid) on the vendored
`lintheme` kit. v1 (`../linshot3`, GTK3/C) is frozen legacy; v2 imports its
data in place (D2). Commit-by-commit history in `changelog.md` (append-only).

| Capability | State | Where |
|---|---|---|
| Studio shell (header / rails / canvas / panels / action bar) | working | `linscreencapture2/window.py` |
| Freeze-frame capture: whole-root grab | working, rig-verified | `core/capture.py` (ctypes libX11) |
| Region select overlay (drag, dim, dashed border, W×H chip, crosshair) | working, rig-verified | `ui/capture_overlay.py` |
| Profiles: Region / Full screen / Delayed 3 s / header Capture | working | `window.py` |
| Window / Scrolling / Pin profiles | inert, status message only | `window.py._profile` |
| Canvas Base layer (fitted draw over checker page) | working | `window.py._draw_canvas` |
| Save PNG (v1 naming, collision-safe) / Copy (clipboard) / Discard | working | `core/capture.py`, `window.py` |
| Icon-button chrome, hover-only labels, 4px-grid spacing | working (r037) | `window.py`, `ui/icons.py` |
| **s044 formation reproduction** (doc header, stateful chip, profile rows, 2-col grouped tools, options-bar formation, top tabs, Layers row, quick styles/steps/navigator footer, Captures menu, summary format, zoom HUD, title, min 720×540) | **landed r042** — render `docs/design/r042_formation_reproduction.png` | `window.py` |
| Compact chrome: 24px standard buttons, colour well on right footer, default window 960×640, scrollable options bar | landed r043 | `window.py` |
| Uniform 16px/24px icons, right-side flyouts, 100px panes | landed r047 | `window.py` |
| **Left sidebar specification** (toggle, dimensions, collapsed consolidation, icon standard) | **documented r048 — section 2b** | `window.py`, HANDOFF 2b |
| Zoom model, options bar content, Layers/Captures/Props panels, tools | stubs / placeholders | see work queue |
| Window snapping in overlay | not ported (v1 phase-3 geometry) | work queue |

## 2. Operator law (normative)

Violations are release blockers. Two directive sets, both recorded in the
ledger and enforced in code review + rig renders:

**r034**: No pill shapes (fully-rounded controls prohibited; radius 6
buttons/inputs, 8 grouped containers, 16 cards; circular allowed only for
canvas content badges). Primary buttons (Capture/Save/Copy) 24px tall.
Keyboard references never on the surface — tooltips or Settings → Keyboard
table only. The captured-images list is named **“Captures”** everywhere
(History is reserved for a future undo panel).

**r037**: Every button is an **icon button**; label text is visible only on
hover via tooltip. Padding/margins must be **even** — 4px grid (4/8/12;
never ad-hoc 5/7/10). Sections/state text may remain as labels (they are not
buttons); buttons themselves carry no text.

## 2a. Design corpus & authority order (r041 deep-dive)

The design intent lives in five places (v1 tree is read-only; r033-era):

| Source | Authority |
|---|---|
| `docs/design/STUDIO-EDITOR-SPEC.md` (r034) | **structure** for v2: regions, 216/280 rails, panel stack, phase map (§5) |
| `s044_studio_editor_graphite_night.html` (linshot3 `docs/design/redesign-2026/`, render in `docs/design/`) | **formation**: exact DOM order of every region, label and control; s045–s048 are theme variants only |
| `linshot3/docs/design/DESIGN-CONTRACT.md` (r027, 25 items) | **component + interaction law** where the v2 spec is silent: overlay (handles, chip docked top-CENTER 32px, magnifier 132px 8×, capture bar Annotate/Copy/Save + hint, freeze chips, end toast), state vocabulary (Ready ✓/Selecting/Captured/Can't-capture), 12 fixed swatch hexes, a11y floors, min window 720×540 |
| `s035`/`s036`/`s037` renders | component sheet, freeze overlay, gallery/Captures reference art |
| `docs/design/linapptemplate/GUI-GUIDE…` + `docs/01–07` | kit-level laws (what·why·next messages, acceptance checklists) |

Operator law **overrides** all of it: r037 labels→tooltips, r034 24px
primaries (contract says 48 — r034 wins, recorded), no pills. Note the
contract's nav-rail/Gallery/Settings structure is **v1-only** — superseded
by the Studio single-window spec.

r039 audit correction: profile ROWS (not grid), 2-col 40×40 tool grid, and
top panel tabs are **spec'd formation** — r037 changes labels, not
formation. They were misclassified as free choices; treat them as
deviations. Size chip belongs top-center above the selection with 4 corner
handles (s044 lines 109–115, 224–226); the v1 top-right chip position we
ported is wrong per s044.

## 2b. Left sidebar specification (r048, verified against code)

The canonical statement of the left sidebar's construction. Constants live
in `window.py` (`LEFT_W`, `LEFT_COLLAPSED_W`); all widths are FIXED PIXELS
— collapse/expand never scale by percentage (r046).

**Toggle.** A 24px caret button in the pane header toggles collapse/expand
(`_toggle_left`): expanded header is `PROFILES ‹`, collapsed state shows a
lone `›` at the top. Toggling rebuilds the pane contents in place; widths
switch between the two fixed constants. The collapse transition is instant
(no animation).

**Dimensions.**

| State | Width | Composition |
|---|---|---|
| Expanded | 100px (`LEFT_W`) | 8px pane margins + 84px content: three 24px columns (4px gaps) whose cells stretch to fill exactly |
| Collapsed | 40px (`LEFT_COLLAPSED_W`) | 8px pane margins + one 24px icon column |

**Icon standard (everywhere, r047).** 16px Phosphor glyph (rasterized at
2× and size-constrained — never stretched, so never blurry) inside a
24×24px button, radius 6. Collapsed, expanded and flyout buttons are
identical. Active state: accent fill + on-accent glyph.

**Expanded contents** (top to bottom, 4px spacing):
1. `PROFILES` header row (10px/0.04em caption + collapse caret).
2. Capture profiles — 6 icons in a 3-column grid (2 rows): Region, Window,
   Full screen, Scrolling, Delayed 3 s, Pin to screen; active profile raised.
3. `TOOLS` caption.
4. Tool groups, each a caption + 3-column grid of 24px cells, separated by
   1px rules: SELECT · DRAW (7) · REDACT (3) · CONTENT (2) · TRANSFORM (4)
   · EDIT (2) per the contract-#4 grouping. Tool click = pick (accent fill).

**Collapsed contents** (one icon per row, stacked under the caret):
consolidated anchors only — `camera` (flyout: all six profiles) plus one
anchor per tool group (`GROUP_ICONS`: cursor/pen/drop-half/chat/rotate/
arrows). Hovering an anchor pops the full group out to the **right**
(`PositionType.RIGHT`) at identical 24px button size, closing after a
220ms grace; flyout items act immediately (arm profile / pick tool).

Right pane parity: `RIGHT_W = 100`, `RIGHT_COLLAPSED_W = 100` (single
state; same icon standard).

## 3. Architecture

Flat packages at repo root; no nested trees. Data flow for a capture:

```
header/profile button -> StudioWindow._start_capture(mode)
  -> hide() + 250ms settle            (window must not be in frame)
  -> core.capture.grab_root()         (ctypes libX11 XGetImage, whole root)
  -> ui.capture_overlay.FreezeOverlay(frame).run(cb)
       [per-monitor undecorated fullscreen windows paint the frozen frame;
        GestureDrag >=5px selects; Esc/Return; seat grab/ungrab]
  -> cb(rect) -> capture.crop(frame, rect)   (normalized + clamped subpixbuf)
  -> canvas Base layer (fitted); Copy = Gdk.Texture -> clipboard;
     Save = save_png() into settings.screenshot_path (v1 shared folder)
```

| Path | Role |
|---|---|
| `linscreencapture2/app.py` | Gtk.Application; NO_AT_BRIDGE before Gtk import (D7) |
| `linscreencapture2/window.py` | StudioWindow shell + capture wiring + APP_CSS (USER priority, D10) |
| `linscreencapture2/core/capture.py` | X11 grab, Rect math (pure), crop, v1 naming, save |
| `linscreencapture2/core/settings.py` | v2 settings.conf with v1 import (D2) |
| `linscreencapture2/core/paths.py` | v1/v2 data locations |
| `linscreencapture2/core/library.py` | read-only v1 library.db handle (D2) |
| `linscreencapture2/ui/capture_overlay.py` | freeze-frame selection overlay |
| `linscreencapture2/ui/icons.py` | Phosphor loader over the full vendored set |
| `lintheme/` | vendored kit (tokens/css/apply/icons); do not modify |
| `assets/icons/phosphor/` | full Phosphor regular set (MIT), SOURCE/LICENSE recorded |
| `tools/rig.sh` | Xephyr rig up/down/status — teardown mandatory |
| `tools/rig_capture_smoke.py` | end-to-end XTEST-driven capture smoke (RIG PASS gate) |
| `tests/` | display-free pytest suite (13 tests) |
| `docs/00-DECISIONS.md` | canonical decision register D1–D10 |
| `docs/design/STUDIO-EDITOR-SPEC.md` | buildable UI spec; §2 r034 rules normative |

## 4. Decision register

Canonical: `docs/00-DECISIONS.md`. Digest: D1 GTK4+Python per operator;
D2 import v1 data in place; D3 vendor lintheme (copy, never reference);
D4 Studio Editor is the UI spec; D5 r034 UI law; D6 capture pixels via
ctypes libX11 (GTK4 removed the Gdk APIs; freeze-frame invariant kept);
D7 NO_AT_BRIDGE app-side; D8 rig drivers root-relative + XTEST; D9 every
button is an icon button + 4px-grid evenness (r037); D10 app CSS loads at
USER priority after `apply.install` (kit CSS is USER; APPLICATION loses
ties — this silently killed accent backgrounds in r037).

## 5. Verification & QA protocol

Every milestone clears all four gates before commit; evidence lands in the
changelog entry and, for UI work, as rig renders in `docs/`.

1. **Unit gate** — `python3 -m pytest -q` (display-free; Rect math, naming,
   settings roundtrip, icon resolution). Current: 13/13.
2. **Compile gate** — `python3 -m compileall -q linscreencapture2 lintheme
   tests tools`.
3. **Rig render gate** (UI changes) — `tools/rig.sh up`; run a render script
   (see §6 snapshot pattern); **inspect the PNG** (chrome, spacing, theme);
   `tools/rig.sh down` — teardown is not optional, the rig window is on the
   operator's desktop.
4. **End-to-end gate** (capture changes) — `HOME=/tmp/lsc2-rig-home
   DISPLAY=:61 python3 tools/rig_capture_smoke.py` must print
   `RIG PASS`: real XTEST drag → exact crop size → pixel-verified content →
   PNG written under the sandbox HOME.

Bookkeeping gate: changelog entry, decisions register, `.zcode/memory/`
update, ledger r-index + session note, D13 backup, commit, push.

## 6. Known pitfalls (each one cost a debug cycle — do not re-learn them)

- **GTK 4.14 API deletions**: no `Gdk.pixbuf_get_from_window`, no
  `Gdk.Screen`, no `set_skip_taskbar_hint`/`set_keep_above`, monitors are a
  ListModel (`display.get_monitors().get_n_items()/get_item(i)`).
- **CSS `var()` unsupported** in 4.14 — lintheme substitutes tokens in
  Python; app must do the same (r034-era `var(--border)` never rendered).
- **CSS provider priority** (D10): kit at USER; app CSS must also be USER
  and installed after `apply.install`.
- **GdkPixbuf crops keep the parent rowstride** — sample pixels via
  `get_rowstride()`, never `w*3`. `Pixbuf.fill()` maps 0xRRGGBB00.
- **muffin resizes the Xephyr root** to host RandR modes (a `-screen
  1280x800` rig becomes 1600×1200): always root-relative geometry (D8).
- **XTEST, not xdotool** (not installed): `ctypes` libXtst fake events.
- **PyGObject signal order**: instance `activate` handlers run *before* a
  `do_activate` override — fetch app windows on a timeout, not in the handler.
- **Freeze-frame invariant**: grab before any window exists; hide the studio
  window (250 ms) first. XGetImage needs exact root dims (query attributes).
- **at-spi CRITICAL** in rigs is killed by `NO_AT_BRIDGE=1` (D7); app output
  must stay free of criticals — check the log every rig run.
- **Live-desktop grabs are not evidence**: on `:0` other windows overlap the
  app (a r040 crop caught a browser sidebar). Render/verify in the rig only;
  use `capture.grab_root()` on the rig display, never on the desktop.
- **DBus app-id uniqueness**: if the desktop instance is running, a rig
  driver using the same `Gtk.Application` id silently no-ops (run()
  returns, activate never fires). Rig drivers set
  `Gio.ApplicationFlags.NON_UNIQUE` (D11, r043).
- **GTK4 layout laws for fixed panes** (r047): (a) expand flags PROPAGATE
  from descendants — buttons with `hexpand` inside a pane make the pane
  itself claim extra space unless the pane pins `set_hexpand(False)`;
  (b) Box AND Grid distribute extra space to non-expanding children up
  to their NATURAL — so a pane is only as fixed as its natural width;
  (c) for wrapping labels, `width_chars` raises the MINIMUM while
  `max_width_chars` caps the NATURAL. Fixed 100px panes = Grid + explicit
  hexpand(False) panes + max_width_chars labels + hexpanding canvas column.

Rig snapshot pattern (render any window state to PNG):

```python
pb = capture.grab_root()          # after window.present() + ~1.2s settle
pb.savev("/tmp/lsc2-rig/<name>.png", "png", [], [])
```

## 7. Work queue

Priority order (per ledger plan, spec §5, and the r041 contract deep-dive);
each item = one r-marker. Formation items (F) make the shell match the
documented intent; behavior items (B) are the scheduled phases.

1. **F — Formation pass** — **LANDED r042** (`docs/design/r042_formation_reproduction.png`).
   Remaining formation scraps, folded into the overlay item and later phases:
   canvas size chip/selection belong to the overlay contract below.
2. **F — Overlay contract items**: 4 corner handles; size chip docked
   top-center above the selection (32px, icon + tabular W×H); freeze-state
   chips top-left ("Selecting on the frozen frame · Esc unfreezes" /
   "Frozen at HH:MM:SS · apps keep running"); capture bar below selection
   (Annotate primary / Copy / Save / "saves as LinCapture_… · Enter copies
   · Esc unfreezes" / ✕) replacing auto-confirm on release; end toast
   ("Captured W×H · copied · saved NAME") instead of bare status; 8×
   magnifier loupe last (biggest lift).
3. **B — Options bar** (spec E1, effort M): segments, 12-swatch content
   palette (contract §9 hexes), toggles, per-tool numerics, shape segment.
4. **B — Panels**: Layers/Captures/Props as real widgets (Captures can be
   library-backed read-only today, D2); quick styles, Steps next-№,
   Navigator minimap footer (s044 pfoot formation).
5. **B — Window snapping** — port v1 phase-3 `window_geometry` (XQueryTree
   via ctypes) into `FreezeOverlay` (click/Enter/arrow-cycle); unblocks the
   Window profile.
6. **B — Annotation object model** (phase 12/15) — tools become real.
7. **B — Zoom model** (percent · Fit · HUD), then Navigator live minimap.
8. **B — PrintScreen global hotkey + hidden-instance relaunch** (v1 parity).
9. **B — Wayland portal capture** (X11-only today; `display_is_x11` guards).
10. **B — Settings > Keyboard table** (spec §2/§4) once shortcuts exist.

## 8. Bookkeeping conventions

- Response markers `[rNNN]` per project; ledger `~/projects/Zai-ZCode/s-register.md`
  r-index must match the latest marker; session note appended per milestone.
- `changelog.md` append-only, one entry per completed change.
- Decisions: `docs/00-DECISIONS.md` (canonical) + `.zcode/memory/decisions.md`
  (digest with rationale); pending queue in `.zcode/memory/pending.md` —
  both updated at session end, never left stale.
- Repo tooling lives in `tools/` without global s-numbers (project rule 3);
  operator-facing one-off scripts outside the repo keep sNNN naming.
- D13 backup after every completed phase and before session close
  (`s009_backup_project.sh`, `-m` describes the work).
- Commits: conventional, one per milestone; push to origin/main after gates.

## 9. Adversarial review checklist

Attack surfaces, in priority order:

1. **Data safety** — Save must never overwrite (`unique_path` collision
   suffix; verify by saving twice within one second). v1 files read-only
   except the shared captures folder written by explicit user action (D2).
2. **Law compliance** — run a rig render; grep `window.py` for any
   `Gtk.Button(label=...)` (should find none); check margins against the
   4px grid; check radius values against D5.
3. **Freeze-frame invariant** — the studio window must never appear in its
   own capture: covered by hide+settle; reviewer should capture with the
   app visible pre-hide (start capture, screenshot fast) and confirm.
4. **Selection math** — property-test `Rect.normalized`/`clamped_to` with
   negative/exterior rects (v1 semantics: ≥5px else cancel).
5. **Resource leaks** — overlay windows destroyed on every finish path
   (accept, Esc, click-cancel, close-request); seat ungrabbed; X display
   closed (`grab_root` opens/closes per call).
6. **Startup hygiene** — zero CRITICALs in app output (at-spi, GTK).
7. **Toolkit assumptions** — anything touching Gdk/Gtk APIs must hold on
   4.14 (see §6 list); reviewer greps for APIs in the §6 deletion set.
