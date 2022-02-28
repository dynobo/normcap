"""Capture screenshot of all screens using DBUS org.gnome.Shell.Screenshot."""

import logging
import tempfile
from pathlib import Path

from PySide6 import QtGui

try:
    from PySide6 import QtDBus

    HAVE_QTDBUS = True
except ImportError:
    HAVE_QTDBUS = False

from normcap.screengrab.utils import split_full_desktop_to_screens

logger = logging.getLogger(__name__)


def get_screenshot_interface():
    if not HAVE_QTDBUS:
        raise ModuleNotFoundError("QtDBUS not available.")

    item = "org.gnome.Shell.Screenshot"
    interface = "org.gnome.Shell.Screenshot"
    path = "/org/gnome/Shell/Screenshot"

    bus = QtDBus.QDBusConnection.sessionBus()
    if not bus.isConnected():
        logger.error("Not connected to dbus!")
    return QtDBus.QDBusInterface(item, path, interface, bus)


def fullscreen_to_file(filename):
    """Capture full screen and store it in file."""
    if not HAVE_QTDBUS:
        raise ModuleNotFoundError("QtDBUS not available.")

    screenshot_interface = get_screenshot_interface()
    if screenshot_interface.isValid():
        x = screenshot_interface.call("Screenshot", True, False, filename)
        if x.errorName():
            logger.error("Failed move Window!")
            logger.error(x.errorMessage())
    else:
        logger.error("Invalid dbus interface")


def grab_screens() -> list[QtGui.QImage]:
    """Capture screenshots for all screens using org.gnome.Shell.Screenshot.

    This methods works gnome-shell < v41 and wayland.
    """
    logger.debug("Use capture method: DBUS Shell")

    _, temp_file = tempfile.mkstemp(prefix="normcap")
    try:
        fullscreen_to_file(temp_file)
        image = QtGui.QImage(temp_file)
    finally:
        Path(temp_file).unlink()

    return split_full_desktop_to_screens(image)
