"""Gtk.Application entry point (GTK4)."""

import os

# kills the at-spi bus CRITICAL seen in the rig (accessibility stays available
# via the desktop bus when the app is launched normally)
os.environ.setdefault("NO_AT_BRIDGE", "1")

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from linscreencapture2 import __version__
from linscreencapture2.window import StudioWindow

APP_ID = "media.mensura.LinScreenCapture2"


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)

    def do_activate(self):
        win = self.props.active_window
        if win is None:
            win = StudioWindow(application=self)
        win.present()


def main():
    app = App()
    app.set_version(__version__)
    return app.run(None)
