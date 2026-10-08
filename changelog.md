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
