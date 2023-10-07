import functools
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Optional

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


def is_wayland_display_manager() -> bool:
    """Identify relevant display managers (Linux)."""
    if sys.platform != "linux":
        return False
    xdg_session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    wayland_display = os.environ.get("WAYLAND_DISPLAY", "").lower()
    return "wayland" in wayland_display or "wayland" in xdg_session_type


@functools.cache
def get_gnome_version() -> Optional[str]:
    """Get gnome-shell version (Linux, Gnome)."""
    gnome_version = ""
    if sys.platform != "linux":
        return None

    if (
        not os.environ.get("GNOME_DESKTOP_SESSION_ID", "")
        and "gnome" not in os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    ):
        return None

    if not shutil.which("gnome-shell"):
        return None

    try:
        output = subprocess.check_output(
            ["gnome-shell", "--version"], shell=False, text=True  # noqa: S607, S603
        )
        if result := re.search(r"\s+([\d.]+)", output.strip()):
            gnome_version = result.groups()[0]
    except Exception as e:
        logger.warning("Exception when trying to get gnome version from cli %s", e)
        return None

    logger.debug("Detected Gnome Version: %s", gnome_version)
    return gnome_version


def has_dbus_portal_support() -> bool:
    gnome_version = get_gnome_version()
    return not gnome_version or gnome_version >= "41"


def has_grim_support() -> bool:
    if not shutil.which("grim"):
        return False
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            completed_proc = subprocess.run(
                [  # noqa: S607
                    "grim",
                    "-g",
                    "0,0 5x5",
                    "-l",
                    "0",
                    f"{temp_dir}{os.pathsep}normcap_test.png",
                ],
                shell=False,  # noqa: S603
                check=False,
                timeout=3,
                text=True,
                capture_output=True,
            )
            grim_supported = completed_proc.returncode == 0
            logger.debug(
                "grim output: stdout=%s, stderr=%s",
                completed_proc.stdout,
                completed_proc.stderr,
            )
        except Exception:
            logger.exception("Couldn't determine grim support.")
            grim_supported = False

    logger.debug("Support for grim is%s available.", "" if grim_supported else " not")
    return grim_supported
