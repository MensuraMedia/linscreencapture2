# Decisions log

| # | Date | Decision | Why |
|---|---|---|---|
| D1 | 2026-10-07 | GTK 4 + Python (PyGObject), per operator | new codebase; v1 (GTK3/C) stays frozen |
| D2 | 2026-10-07 | Import v1 data in place: settings from ~/.config/linshot, captures folder + library.db reused | operator choice; no data migration |
| D3 | 2026-10-07 | Vendor lintheme at repo root (kit per linapptemplate); app CSS separate from kit CSS | copy-don't-reference doctrine |
| D4 | 2026-10-07 | Studio Editor (mockups s044-s048, STUDIO-EDITOR-SPEC.md) is the v2 UI spec | operator-approved direction |
| D5 | 2026-10-07 | UI rules: no pill shapes; shortcut hints hover-only or Settings > Keyboard table; primary buttons 24px; image list named "Captures" | operator directives r034 |
| D6 | 2026-10-07 | Capture pixels via ctypes libX11 (XGetImage port of v1 screen_capture.c) | GTK4 removed Gdk.pixbuf_get_from_window/Gdk.Screen; keeps v1 freeze-frame invariant; Wayland portal later |
| D7 | 2026-10-07 | NO_AT_BRIDGE=1 app-side before Gtk import | kills the rig at-spi CRITICAL; setdefault still honors an explicit override |
| D8 | 2026-10-07 | Rig drivers use root-relative geometry + ctypes XTEST (no xdotool) | muffin resizes the Xephyr root to host RandR modes; fixed coords go stale |
| D9 | 2026-10-07 | Every button is an icon button (label hover-only); even padding/margins on a 4px grid | operator directive r037 |
| D10 | 2026-10-07 | App CSS loads at USER priority after apply.install | kit CSS is USER priority; APPLICATION loses ties and kit rules silently override app rules |
