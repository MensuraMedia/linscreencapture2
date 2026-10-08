# Decisions

Record architectural decisions with rationale. Newest at the bottom.

## D6 (r035): capture pixels via ctypes libX11, not GDK

GTK4 (4.14 here) removed Gdk.pixbuf_get_from_window and Gdk.Screen, so
core/capture.py ports v1 screen_capture.c directly: XOpenDisplay ->
XGetImage(root, exact XWindowAttributes dims) -> pixbuf. Keeps the v1
phase-1 freeze-frame invariant (grab before any window exists) and stays
X11-only; Wayland portal is a later, separate port. Standard
LE/BGRX layouts convert via C-speed bytearray slices; exotic masks fall
back to numpy (present on this machine) or a pure loop.

## D7 (r035): NO_AT_BRIDGE=1 set app-side before Gtk import

Kills the rig at-spi CRITICAL (recorded r034). setdefault respects an
explicit env override. Tradeoff accepted: no AT bridge inside the app
process unless the desktop sets the variable itself.

## D8 (r035): rig facts that bite again

- muffin resizes the Xephyr root to host RandR modes (a "-screen
  1280x800" rig becomes 1600x1200 once muffin starts). Rig drivers must
  use root-relative geometry, never fixed coordinates.
- GdkPixbuf new_subpixbuf+copy keeps the PARENT rowstride; sample rows
  via get_rowstride(), not w*3.
- PyGObject: instance "activate" handlers run BEFORE a do_activate
  override; pick up app windows on a timeout, not in the handler.
- xdotool absent; drive rigs with ctypes XTEST (tools/rig_capture_smoke.py).

