"""Display-free smoke tests: package integrity + v1 import helpers."""
import configparser
from pathlib import Path

from linscreencapture2 import __version__
from linscreencapture2.core import paths, settings


def test_version():
    assert __version__.startswith("2.0.0")


def test_tokens_vendored():
    from lintheme import tokens

    assert tokens.NAME == "Graphite Night"
    assert tokens.COLOR["bg"] == "#1c1f23"


def test_settings_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "V2_CONFIG_DIR", tmp_path)
    s = settings.Settings(screenshot_path="/tmp/caps", capture_delay=3)
    s.save()
    s2 = settings.Settings.load()
    assert s2.screenshot_path == "/tmp/caps"
    assert s2.capture_delay == 3


def test_v1_settings_parse(tmp_path):
    conf = tmp_path / "settings.conf"
    conf.write_text("[Settings]\nscreenshot_path=/data/caps\n")
    cp = configparser.ConfigParser()
    cp.read(conf)
    assert cp["Settings"]["screenshot_path"] == "/data/caps"
