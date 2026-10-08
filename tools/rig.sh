#!/usr/bin/env bash
# rig.sh - Xephyr test-rig control for LinScreenCapture 2 (D8 rig facts apply).
# Usage:
#   tools/rig.sh up      start Xephyr :61 + muffin (idempotent)
#   tools/rig.sh down    stop the rig and remove its locks
#   tools/rig.sh status  report whether the rig is running
# ALWAYS run `tools/rig.sh down` when a render/verification session ends -
# the rig window is visible on the operator's desktop and must not linger.
set -u
DISP=":61"

running() { pgrep -f "Xephyr $DISP" >/dev/null; }

case "${1:-status}" in
  up)
    if running; then echo "rig already up"; exit 0; fi
    rm -f /tmp/.X61-lock /tmp/.X11-unix/X61
    Xephyr $DISP -screen 1280x800 -ac >/tmp/xephyr61.log 2>&1 &
    sleep 2
    if ! running; then echo "Xephyr failed to start - see /tmp/xephyr61.log"; exit 1; fi
    DISPLAY=$DISP muffin --replace >/tmp/muffin61.log 2>&1 &
    sleep 2
    echo "rig up on $DISP ($(DISPLAY=$DISP xwininfo -root 2>/dev/null | awk '/Width|Height/' | tr -d ' \n' | tr '\n' ' '))"
    ;;
  down)
    pkill -f "Xephyr $DISP" 2>/dev/null
    pkill -f "muffin" 2>/dev/null
    sleep 0.5
    rm -f /tmp/.X61-lock /tmp/.X11-unix/X61
    echo "rig down"
    ;;
  status)
    if running; then echo "rig up"; else echo "rig down"; fi
    ;;
  *)
    echo "usage: tools/rig.sh {up|down|status}"; exit 2
    ;;
esac
