"""Display-free test: every icon referenced by the shell resolves."""
from linscreencapture2.ui import icons
from linscreencapture2.window import PANEL_ICONS, PROFILE_ICONS, TOOL_ICONS

EXTRA = ["camera", "minus", "plus", "arrows-in", "trash", "stack", "images",
         "copy", "download-simple"]


def test_all_button_icons_exist():
    names = set(names_ := icons.names())
    for label, icon in {**PROFILE_ICONS, **TOOL_ICONS, **PANEL_ICONS}.items():
        assert icon in names, f"{label} -> missing icon {icon}"
    for icon in EXTRA:
        assert icon in names, f"missing icon {icon}"


def test_pixbuf_renders_at_requested_size():
    assert icons.pixbuf("camera", 14).get_width() == 14
    assert icons.pixbuf("crop", 20).get_height() == 20
