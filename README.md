# LinScreenCapture 2

GTK4 / Python screenshot tool with the **Studio Editor** - a Photoshop x
Snagit hybrid: capture profiles + tool palette on the left, layers /
captures / properties panels on the right, contextual options bar on top.

- Framework: [linapptemplate](https://github.com/MensuraMedia/linapptemplate)
  (`lintheme` kit vendored in `lintheme/`, version in `lintheme/__init__.py`)
- Toolkit: GTK 4 via PyGObject, Python 3.10+
- Design: `docs/design/STUDIO-EDITOR-SPEC.md` + mockups `s044-s048`
- v1 lineage: imports settings and the capture library from linshot3 in
  place (decision D2, `docs/00-DECISIONS.md`)

## Run (dev)

    PYTHONPATH=. python3 -m linscreencapture2

## Test

    python3 -m pytest -q

## Layout

    lintheme/            theme kit (tokens <- css/status/icons <- apply)
    linscreencapture2/   the app (app.py, window.py, ui/, core/)
    docs/                adopting guide, Studio spec, decisions
    tests/               pytest suite
