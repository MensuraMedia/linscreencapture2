"""Display-free tests for the colour picker helpers (r051)."""
from linscreencapture2.window import _parse_hex, _to_hex


def test_parse_hex_forms():
    assert _parse_hex("#6f19e6") == (0x6F, 0x19, 0xE6)
    assert _parse_hex("6f19e6") == (0x6F, 0x19, 0xE6)
    assert _parse_hex("#f00") == (0xFF, 0x00, 0x00)


def test_parse_hex_rejects_garbage():
    assert _parse_hex("nope") is None
    assert _parse_hex("#12345") is None
    assert _parse_hex("#zzzzzz") is None


def test_to_hex_roundtrip():
    assert _to_hex((0x6F, 0x19, 0xE6)) == "#6f19e6"
    assert _parse_hex(_to_hex((1, 2, 3))) == (1, 2, 3)
