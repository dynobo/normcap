"""Some utility functions."""

import logging
import tempfile
from pathlib import Path

from jeepney import MessageType  # type: ignore
from jeepney.io.blocking import open_dbus_connection  # type: ignore
from jeepney.wrappers import (  # type: ignore
    DBusErrorResponse,
    MessageGenerator,
    new_method_call,
)
from PySide6 import QtGui, QtWidgets

from normcap.screengrab.utils import split_full_desktop_to_screens

logger = logging.getLogger(__name__)


class GnomeShellScreenshot(MessageGenerator):
    """Capture screenshot through dbus."""

    interface = "org.gnome.Shell.Screenshot"

    def __init__(self):
        """Init jeepney message generator."""
        super().__init__(
            object_path="/org/gnome/Shell/Screenshot",
            bus_name="org.gnome.Shell.Screenshot",
        )

    def grab(self, filename):
        """Grab specific section to file with flash disabled."""
        return new_method_call(
            self,
            "Screenshot",
            "bbs",
            (True, False, filename),
        )

    def grab_rect(self, x, y, width, height, filename):
        """Grab specific section to file with flash disabled."""
        return new_method_call(
            self,
            "ScreenshotArea",
            "iiiibs",
            (x, y, width, height, False, filename),
        )


def grab_full_desktop() -> QtGui.QImage:
    """Capture rect of screen on gnome systems using wayland."""
    virtual_geometry = QtWidgets.QApplication.primaryScreen().virtualGeometry()
    x = virtual_geometry.x()
    y = virtual_geometry.y()
    width = virtual_geometry.width()
    height = virtual_geometry.height()

    _, temp_file = tempfile.mkstemp(prefix="normcap")
    try:
        msg = GnomeShellScreenshot().grab_rect(x, y, width, height, temp_file)
        connection = open_dbus_connection(bus="SESSION")
        result = connection.send_and_get_reply(msg)
        if result.header.message_type == MessageType.error:
            logger.error("Screenshot with DBUS failed: %s", ", ".join(result.body))
            raise RuntimeError("DBUS returned failure.")

        image = QtGui.QImage(temp_file)

    except DBusErrorResponse as e:
        if "invalid params" in [d.lower() for d in e.data]:
            logger.info("ScreenShot with DBUS failed with 'invalid params'.")
        else:
            logger.exception("ScreenShot with DBUS failed with exception.")
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
