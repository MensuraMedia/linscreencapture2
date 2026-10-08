# Studio Editor — Technical Specification (r034)

Supporting document for the Photoshop × Snagit hybrid editor re-imagination
(mockups s044–s048, generator `~/projects/Zai-ZCode/s043_studio_editor_mockups.py`,
renders in `_render/`). This spec is buildable against the phase-6.5 shell
(`src/ui_shell.c`) and the scheduled phases. Operator directives of 2026-10-07
(r034) are incorporated as normative rules in §2.

## 1. Design thesis

One editor surface, two DNA strands, no mode switching:

- **Photoshop strand** — precision: a dense tool palette, a contextual
  options bar, a stacked panel column (Layers / Captures / Props), a
  navigator, and a zoom model (percent · Fit · 8× hover zoom).
- **Snagit strand** — speed: capture profiles that arm a capture in one
  click, quick styles that apply a look in one click, steps auto-numbering,
  and an action bar that always ends in Copy / Save.

Everything is non-destructive: annotations and FX are objects (layers)
until Flatten. The canvas always shows the frozen-frame capture that phase 1
guarantees.

## 2. Normative UI rules (r034 directives)

| Rule | Spec |
|---|---|
| Primary button size | Capture and Save are **24px tall** (50% of the previous 48px), font 12px, padding 0 10/12px, radius 6. Icon 14px. |
| Keyboard references | **Never rendered on the surface.** Shortcut letters, Alt-switches, hotkey names appear only (a) in tooltips on hover, or (b) in **Settings → Keyboard** as a table (action · keys · context). The doc-sub, status chip, tool buttons, and step hints carry none. |
| Image-history naming | The captured-images list is **“Captures”** everywhere (panel tab, action-bar menu, nav destination, window titles). “History” is reserved for undo steps if a dedicated undo panel is added later. |
| Shape language | **No pill shapes.** Fully-rounded (radius ≥ ½ height) controls are prohibited. All controls are rounded squares: radius 6 for buttons/inputs, 8 for grouped containers (zoom control), 16 for cards. Canvas annotation badges (step №) remain circular — they are content, not chrome. |
| Hover-only hints | Any hint that explains a hover behavior (e.g. “8× zoom”) lives in the element's tooltip, not as permanent text. |

## 3. Layout regions (1280×800 reference)

```
┌────────────────────────────────────────────────────────────────────┐
│ Header 48   doc title+sub · status chip · ⋯ · zoom · Capture (24)  │
├───────────┬───────────────────────────────────────────┬────────────┤
│ LEFT 216  │ OPTIONS BAR 40 (active tool controls)      │ RIGHT 280  │
│ Capture   ├───────────────────────────────────────────┤ Layers │   │
│ profiles  │ CANVAS (checker, selection, FX overlays,  │ Captures│  │
│ Tools 2×n │ size chip, zoom HUD)                      │ Props  │  │
│ color well│                                           │ Styles,│  │
│           │                                           │ Steps, │  │
│           │                                           │ Nav    │  │
├───────────┴───────────────────────────────────────────┴────────────┤
│ Action bar 48  Discard · Flatten · Captures ▾ · ⋯ · summary · Copy · Save │
└────────────────────────────────────────────────────────────────────┘
```

- Left rail 216px: Capture Profiles section (6 rows, active = raised +
  accent icon), Tools section (2-column grid, 40×40 cells, icon 20px
  muted / on-accent when active; shortcuts in tooltip only), color well
  (foreground over background, swap = X).
- Options bar 40px: icon + tool name, segments (e.g. Thin/Body/Chunky),
  12-swatch content palette (20×20, 3px radius, 4px gaps, ring on
  selected), toggles (Shadow), per-tool numerics (Head 1.0×), shape
  segment (Square/Rounded). Content swaps per active tool (E1 registry).
- Canvas column: checkerboard page, capture centered at zoom, selection
  with 4 corner handles + size chip (top-center, 28px, rounded 6), zoom
  HUD (bottom-left, 28px, rounded 6: percent · Fit).
- Right column 280px, panel tabs **Layers | Captures | Props**:
  - Layers: rows (24×20 thumb · name · kind chip · eye), top-to-bottom
    z-order, FX layers (blur/pixelate) render with an FX chip; selection
    drives the options bar.
  - Captures: versioned saves of this image (per-capture generations) —
    the entry point for “re-open editable” (phase 6 layers) and the
    gallery is the cross-capture library (phase 19).
  - Props: active-tool numeric/behavior settings (arrow head scale, blur
    intensity, text font…).
  - Footer: Quick styles (4 presets), Steps next-№, Navigator minimap.
- Action bar 48px: Discard (danger ghost) · Flatten · Captures ▾ ·
  spacer · summary (“W×H · PNG · N layers · N FX · zoom%”) · Copy ·
  Save — Save/Copy 24px as per §2.

## 4. Interaction model

1. **Capture:** arm a profile (left) or press PrintScreen → freeze (phase
   1 invariant) → region select with size chip → options bar preview →
   confirm → editor opens with the capture as Base layer.
2. **Annotate:** pick tool (palette) → adjust in options bar → drag on
   canvas → each drag creates a layer (phase 12 object model).
3. **Restyle:** select a layer → Quick Styles or options bar re-style it
   in place (non-destructive until Flatten).
4. **Finish:** Copy (clipboard) or Save (file + Captures version + library
   index). End toast (6.5b): “Captured W×H · copied · saved name”.
5. **Keyboard:** all shortcuts are discoverable in tooltips and in
   Settings → Keyboard (table: action · keys · context). No on-surface
   key hints (§2).

## 5. Data model → build-phase mapping

| Studio concept | Backing phases | Status |
|---|---|---|
| Layers panel, FX layers | 12 object model · 15 z-order | scheduled |
| Captures panel / versions | 6 library (valid_hash, versions) | **landed** (library.db) |
| History / undo | 16 redo + history | scheduled |
| Quick styles | 18 tool style presets | scheduled |
| Steps auto-№ | 8 numbered badges | scheduled |
| Scrolling profile | 22 scrolling capture (experimental) | scheduled |
| Region/Window/Full/Delay/Pin | 1–5 + 20 (pin) | **landed** (pin = 20) |
| Options bar per-tool controls | 7–11 (alpha, badges, redaction, eyedropper, fill) | scheduled |

## 6. Theming

Five token sets (s032 palettes) — Graphite Night (default), Mint Daylight,
Paper & Ink, CMYK Studio, High Contrast. Components consume tokens only;
the content palette (12 swatches) is identical across themes. High
Contrast keeps 1px white borders and forbids hover-only affordance loss.

## 7. Accessibility

- Text ≥12px; muted #aab2bd-on-#262a30 ≈ 6.8:1 (≥ 4.5:1 floor).
- Interactive ≥ 24px after the r034 button reduction (primary 24px is the
  operator-directed exception to the 32px floor — recorded).
- Keyboard references: hover tooltips + Settings → Keyboard table.
- No pill shapes (r034); radius 6/8/16 per component class.

## 8. Implementation deltas from the phase-6.5 shell

| Delta | Effort | Where |
|---|---|---|
| Capture/Save 24px; action bar 48px | S | ui_shell.c CSS |
| De-pill chip/zoom (radius 6/8) | S | ui_shell.c CSS |
| Nav “Gallery” → “Captures” | S | main_window.c nav defs |
| Doc-sub without Alt+1; chip text “Ready” | S | ui_shell.c |
| Options bar (per-tool controls out of the side panel) | M | new `options_bar` section in ui_shell + move colors-page controls |
| Layers/Captures/Props panel stack | M–L | phases 12/15/16 + library |
| Capture profiles in-rail | S | reuses capture_mode + delay + pin(20) |
| Command palette (Ctrl+K) | M | new scope — needs operator nod |
