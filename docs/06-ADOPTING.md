# 6. Adopting lintheme in a Lin* app

## 6.1 Steps

1. **Copy** `lintheme/` into the app (e.g. `src/lintheme/`). Copy, don't reference: the app must
   keep working if this repository moves. Record the kit version (`lintheme.__version__`) in the
   app's decisions log.
2. **Dependencies**: add the runtime packages from [01-STACK.md](01-STACK.md) to the app's
   `app.json` → `offline` and its installer's package list.
3. **Install the theme** once the window exists: `apply.install(window)` (or build on
   `DashboardWindow`, which does it). Remove the app's old theme CSS and colour constants.
4. **Shell**: replace the app's sidebar and header with `DashboardWindow` and four destinations.
5. **Pages**: rebuild each page from components (cards, field rows, segmented choices, banners,
   action bar). Keep the app's own managers and backends untouched: only the UI layer changes.
6. **Status**: map the app's device states onto `ok / busy / attention / error / none` and drive
   `window.chip.set_status(...)` from the existing status poll.
7. **Messages**: rewrite user-facing strings in the what · why · next-step pattern; add a test that
   runs `status.problems()` over them.
8. **Verify**: lint, tests (`xvfb-run`), headless screenshots of every page and state, a keyboard-only
   pass, and the app's real device. Commit screenshots.

## 6.2 Where each app's pages map

| App | Job page | Device page specifics |
|---|---|---|
| LinPrinter | Print: options + live preview + Print bar | ink gauges, link health, test pages, printer's own page, stray queues |
| LinScanner | Scan: source, sides, resolution, format + scan preview + Scan bar | feeder state, eSCL/SANE route, calibration |
| LinFileCopy | Copy: source/target + plan preview + Run bar | drives with capacity gauges |
| Any new Lin* utility | the one job it does + its preview + one main action | its device's health and upkeep |

## 6.3 LinPrinter plan (done: LinPrinter 0.3.0 with kit 1.2.7, merged to main 2026-10-05)

On a new branch, `feat/0.3.0-redesign` (not merged until the user is fully satisfied):

1. Vendor `lintheme` into `src/lintheme/`; add `librsvg2-common` and `fonts-ubuntu` to `app.json`
   and `install.sh`.
2. Replace `ui/app_window`, `ui/sidebar` and the themes config with `DashboardWindow`
   (Print, Activity, Printer, Settings); drop the four other themes.
3. Print page: Printer · Document · Paper · Output cards, preview merged in, sticky action bar.
4. Activity page: Queue and Recent merged.
5. Printer page: hero, ink and paper, connection health with the link test, upkeep, defaults,
   details; the Troubleshooter flow.
6. Settings: Printing, optional features, privacy and diagnostics, About.
7. Tests, walkthrough screenshots, docs, `.deb`, version 0.3.0.
