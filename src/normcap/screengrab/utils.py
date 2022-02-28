import functools
import logging
import os
import re
import subprocess
import sys
from typing import Optional

from packaging import version
from PySide6 import QtCore, QtGui, QtWidgets

logger = logging.getLogger(__name__)


def split_full_desktop_to_screens(full_image: QtGui.QImage) -> list[QtGui.QImage]:
    """Split full desktop image into list of images per screen.

    Also resizes screens according to image:virtual-geometry ratio.
    """
    virtual_geometry = QtWidgets.QApplication.primaryScreen().virtualGeometry()

    ratio = full_image.rect().width() / virtual_geometry.width()

    logger.debug("Virtual geometry width: %s", virtual_geometry.width())
    logger.debug("Image width: %s", full_image.rect().width())
    logger.debug("Resize ratio: %s", ratio)

    images = []
    for screen in QtWidgets.QApplication.screens():
        geo = screen.geometry()
        region = QtCore.QRect(
            int(geo.x() * ratio),
            int(geo.y() * ratio),
            int(geo.width() * ratio),
            int(geo.height() * ratio),
        )
        image = full_image.copy(region)
        images.append(image)

    return images


def display_manager_is_wayland() -> bool:
    """Identify relevant display managers (Linux)."""
    if sys.platform != "linux":
        return False
    XDG_SESSION_TYPE = os.environ.get("XDG_SESSION_TYPE", "").lower()
    WAYLAND_DISPLAY = os.environ.get("WAYLAND_DISPLAY", "").lower()
    return "wayland" in WAYLAND_DISPLAY or "wayland" in XDG_SESSION_TYPE


@functools.lru_cache()
def gnome_shell_version() -> Optional[version.Version]:
    """Get gnome-shell version (Linux, Gnome)."""
    if sys.platform != "linux":
        return None

    if (
        os.environ.get("GNOME_DESKTOP_SESSION_ID", "") == ""
        and "gnome" not in os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    ):
        return None

    shell_version = None
    try:
        output_raw = subprocess.check_output(["gnome-shell", "--version"], shell=False)
        output = output_raw.decode().strip()
        if result := re.search(r"\s+([\d.]+)", output):
            shell_version = version.parse(result.groups()[0])
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Exception when trying to get gnome-shell version %s", e)
    return shell_version
