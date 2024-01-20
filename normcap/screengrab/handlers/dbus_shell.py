"""Capture screenshot of all screens using DBUS org.gnome.Shell.Screenshot."""
# ONHOLD: Remove dbus_shell in 2025 (Superseded by dbus_portal, Ubuntu 20.04 needs it)

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Union, cast

from PySide6 import QtGui

try:
    from PySide6 import QtDBus

except ImportError:
    QtDBus = cast(Any, None)

from normcap.screengrab.post_processing import split_full_desktop_to_screens

logger = logging.getLogger(__name__)

install_instructions = ""


def _get_screenshot_interface():  # noqa: ANN202
    if not QtDBus:
        raise ModuleNotFoundError("QtDBUS not available.")

    item = "org.gnome.Shell.Screenshot"
    interface = "org.gnome.Shell.Screenshot"
    path = "/org/gnome/Shell/Screenshot"

    bus = QtDBus.QDBusConnection.sessionBus()
    if not bus.isConnected():
        logger.error("Not connected to dbus!")
    return QtDBus.QDBusInterface(item, path, interface, bus)


def _fullscreen_to_file(filename: Union[os.PathLike, str]) -> None:
    """Capture full screen and store it in file."""
    if not QtDBus:
        raise ModuleNotFoundError("QtDBUS not available.")

    screenshot_interface = _get_screenshot_interface()
    if screenshot_interface.isValid():
        result = screenshot_interface.call("Screenshot", True, False, filename)
        if result.errorName():
            logger.error("Failed move Window!")
            logger.error(result.errorMessage())
    else:
        logger.error("Invalid dbus interface")


def is_compatible() -> bool:
    return True


def is_installed() -> bool:
    return True


def capture() -> list[QtGui.QImage]:
    """Capture screenshots for all screens using org.gnome.Shell.Screenshot.

    This methods works gnome-shell < v41 and wayland.
    """
    _, temp_file = tempfile.mkstemp(prefix="normcap")
    try:
        _fullscreen_to_file(temp_file)
        image = QtGui.QImage(temp_file)
    finally:
        Path(temp_file).unlink()

    return split_full_desktop_to_screens(image)
