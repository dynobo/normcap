"""Some utility functions."""

import logging
import tempfile
from pathlib import Path

from PySide6 import QtGui, QtWidgets

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


def grab(filename):
    """Grab specific section to file with flash disabled."""
    screenshot_interface = get_screenshot_interface()
    if screenshot_interface.isValid():
        x = screenshot_interface.call("Screenshot", True, False, filename)
        if x.errorName():
            logger.error("Failed move Window!")
            logger.error(x.errorMessage())
    else:
        logger.error("Invalid dbus interface")
    return x.arguments()[1]


def grab_rect(x, y, width, height, filename):
    if not HAVE_QTDBUS:
        raise ModuleNotFoundError("QtDBUS not available.")

    screenshot_interface = get_screenshot_interface()
    if screenshot_interface.isValid():
        x = screenshot_interface.callWithArgumentList(
            QtDBus.QDBus.AutoDetect,
            "ScreenshotArea",
            [x, y, width, height, False, filename],
        )
        if x.errorName():
            logger.error("Failed move Window!")
            logger.error(x.errorMessage())
    else:
        logger.error("Invalid dbus interface")

    return x.arguments()[1]


def grab_full_desktop() -> QtGui.QImage:
    """Capture rect of screen on gnome systems using wayland."""
    virtual_geometry = QtWidgets.QApplication.primaryScreen().virtualGeometry()
    # TODO: Use grab instead grab_rect? Test on multi monitor!
    x = virtual_geometry.x()
    y = virtual_geometry.y()
    width = virtual_geometry.width()
    height = virtual_geometry.height()

    _, temp_file = tempfile.mkstemp(prefix="normcap")
    try:
        temp_file = grab_rect(x, y, width, height, temp_file)
        image = QtGui.QImage(temp_file)
    finally:
        Path(temp_file).unlink()

    return image


def grab_screens() -> list[QtGui.QImage]:
    """Capture screenshots for all screens using org.gnome.Shell.Screenshot.

    This methods works gnome-shell < v41 and wayland.
    """
    logger.debug("Use capture method: DBUS Shell")
    full_image = grab_full_desktop()
    return split_full_desktop_to_screens(full_image)
