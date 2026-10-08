# LinScreenCapture 2 — project instructions

Workspace scope. Global standards load first from ~/.zcode/AGENTS.md; this file
only adds what is specific to this project. Additive changes only — never modify
universal standards here.

- Description: GTK4/Python screenshot tool — Studio Editor (Photoshop x Snagit hybrid) on the linapptemplate framework
- Bootstrapped: 2026-10-07 by s003_workspace_bootstrap.sh
- Ledger: ~/projects/Zai-ZCode/s-register.md

## Stack
(fill in: languages, frameworks, package manager, build/test/lint commands)

## Project rules
(add project-specific rules as new entries; do not restate global rules)

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
