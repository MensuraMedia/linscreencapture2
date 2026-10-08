# LinScreenCapture 2 — project instructions

Workspace scope. Global standards load first from ~/.zcode/AGENTS.md; this file
only adds what is specific to this project. Additive changes only — never modify
universal standards here.

- Description: GTK4/Python screenshot tool — Studio Editor (Photoshop x Snagit hybrid) on the linapptemplate framework
- Bootstrapped: 2026-10-07 by s003_workspace_bootstrap.sh
- Ledger: ~/projects/Zai-ZCode/s-register.md

## Stack
- Language: Python 3.10+ (system python3), GUI: GTK 4 via PyGObject (gi)
  on X11 (ctypes libX11 for capture pixels; Wayland portal is future work).
- Icons: Phosphor regular SVGs, vendored full set at
  assets/icons/phosphor/regular (loaded app-side via
  linscreencapture2/ui/icons.py; lintheme's curated subset stays stock).
- Theme: vendored lintheme kit (tokens -> generated CSS -> apply.install).
- Tests: `python3 -m pytest -q` (pyproject pythonpath=["."]); display-free.
- Gates: pytest + `python3 -m compileall -q linscreencapture2 lintheme tests tools`.
- Run: `python3 -m linscreencapture2`. Rig: `tools/rig.sh up|down|status`
  (Xephyr :61 + muffin; driver: `tools/rig_capture_smoke.py`).
- No package manager lockfile; system packages only (python3-gi, gir1.2-gtk-4.0,
  x11-apps, xephyr, muffin). No pip installs required.

## Project rules
(new entries append; never restate or edit earlier ones)

1. UI law (operator r037): EVERY button is an icon button - labels live
   only in tooltips (hover). Even padding/margins on a 4px grid (4/8/12).
   Carried from r034: no pill shapes (radius 6 controls / 8 groups / 16
   cards); primary buttons 24px tall; keyboard hints hover-only or
   Settings > Keyboard; the images list is named "Captures".
2. App CSS loads at USER priority AFTER apply.install (kit CSS is USER;
   APPLICATION loses ties - r038 fix). Tokens are substituted Python-side
   (GTK 4.14 has no CSS var()).
3. Repo tooling lives in tools/ without global s-numbers (project-code
   precedent set r035). Rig teardown is mandatory: `tools/rig.sh down`
   when a render/verification session ends - the rig window shows on the
   operator's desktop.
4. Frozen frame invariant (v1 phase 1): grab_root() strictly before any
   overlay window exists; the studio window hides (250 ms) pre-freeze.
5. Icons (operator r044): Phosphor regular only, from the master local
   source ~/projects/assets/icons/regular; sync by copy into
   assets/icons/phosphor/regular (copy, not reference). No other icon
   type anywhere. Icons render at 2x and constrain to display size
   (never stretch a smaller texture - that is what blurred buttons);
   glyphs are ink-normalized 10px marks (r060) on STANDARDIZED 24x24
   buttons (26px measured outer) - no other button size for icon
   controls; swatch squares share the 24px standard.
6. Layout (operator r052): NO bottom action bar - the action icons
   (Discard/Flatten/Captures/Copy/Save) live in the lower left of the
   left sidebar (grid when expanded, stacked when collapsed). Capture
   summary (WxH/PNG/layers) lives in the header doc sub-line.
7. Captions and stage (operator r055/r057): every button hover caption
   is a SINGLE WORD (status-chip tooltips keep their detail). Sidebar
   tool segments carry no text titles (groups are separated by rules
   only). The canvas stage background is #242424; captures render at
   ORIGINAL size (never auto-fit) and ctrl+mouse-wheel zooms (0.1x-8x,
   live % in the HUD and header).
8. Buttons and tooltips (operator r059): buttons are SQUARE - no
   border-radius anywhere on button chrome; glyphs 12px. NO hover
   flyouts - when a sidebar is closed, ALL of its buttons are listed
   stacked (overflow is reached by expanding; never a scroller).
   Tooltips: flat #141414 background, 11px text, square.

## Change tracking
- changelog.md at repo root — append-only; every completed change gets an entry

## Memory
- .zcode/memory/decisions.md — architectural decisions with rationale
- .zcode/memory/pending.md — unfinished work carried between sessions

## Project specifics (linscreencapture2)

- Toolkit: GTK 4 via PyGObject, Python 3.10+. v1 (../linshot3, GTK3/C) is
  frozen legacy - do not modify it; this project supersedes it.
- Framework: linapptemplate `lintheme` kit, vendored at `lintheme/`
  (record version in lintheme/__init__.py; update via copy, never reference).
- UI spec: docs/design/STUDIO-EDITOR-SPEC.md + mockups s044-s048 (renders in
  ../linshot3/docs/design/redesign-2026/_render/ and copied render
  docs/design/). Studio Editor = Photoshop x Snagit hybrid (see mockups).
- UI law (operator r034): NO pill shapes (rounded squares, radius 6/8);
  keyboard hints hover-only or Settings > Keyboard table; primary buttons
  24px; the captured-images list is named "Captures" (not History/Gallery).
- Data: import v1 in place (D2) - settings ~/.config/linshot/settings.conf,
  captures folder + library.db reused. Never write to v1 files from v2
  except the shared captures folder by user action.
- Layout: flat packages at repo root (lintheme/, linscreencapture2/),
  black line-length 110, pytest via pythonpath=["."], compileall gate.
- No cloud/network/telemetry ever. No commits to ../linshot3.
