"""Display-free test: every icon referenced by the shell resolves."""
from linscreencapture2.ui import icons
from linscreencapture2.window import (PANEL_PAGES, PROFILE_META, QUICK_STYLES,
                                      TOOL_GROUPS, TOOL_NAMES)

EXTRA = ["camera", "minus", "plus", "arrows-in", "trash", "stack", "images",
         "copy", "download-simple", "swap", "caret-down", "eye"]


def test_all_button_icons_exist():
    names = icons.names()
    for name, (icon, _meta) in PROFILE_META.items():
        assert icon in names, f"profile {name} -> missing icon {icon}"
    for group, tools in TOOL_GROUPS:
        for label, icon in tools:
            assert icon == TOOL_NAMES[label], f"{label} map mismatch"
            assert icon in names, f"tool {label} -> missing icon {icon}"
    for name, (icon, _page) in PANEL_PAGES.items():
        assert icon in names, f"panel {name} -> missing icon {icon}"
    for _name, _hexc in QUICK_STYLES:
        pass
    for icon in EXTRA:
        assert icon in names, f"missing icon {icon}"


def test_pixbuf_renders_at_requested_size():
    assert icons.pixbuf("camera", 14).get_width() == 14
    assert icons.pixbuf("crop", 20).get_height() == 20


def test_content_palette_matches_contract():
    from linscreencapture2.window import CONTENT_COLORS
    assert CONTENT_COLORS[0] == "#e5484d" and CONTENT_COLORS[8] == "#e58fb1"
    assert len(CONTENT_COLORS) == 12
