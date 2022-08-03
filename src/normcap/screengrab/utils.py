import functools
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
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


def _display_manager_is_wayland() -> bool:
    """Identify relevant display managers (Linux)."""
    if sys.platform != "linux":
        return False
    XDG_SESSION_TYPE = os.environ.get("XDG_SESSION_TYPE", "").lower()
    WAYLAND_DISPLAY = os.environ.get("WAYLAND_DISPLAY", "").lower()
    return "wayland" in WAYLAND_DISPLAY or "wayland" in XDG_SESSION_TYPE


def _get_gnome_version_xml() -> str:
    gnome_version_xml = Path("/usr/share/gnome/gnome-version.xml")
    if gnome_version_xml.exists():
        return gnome_version_xml.read_text(encoding="utf-8")

    raise FileNotFoundError


@functools.lru_cache()
def get_gnome_version() -> Optional[version.Version]:
    """Get gnome-shell version (Linux, Gnome)."""
    if sys.platform != "linux":
        return None

    if (
        os.environ.get("GNOME_DESKTOP_SESSION_ID", "") == ""
        and "gnome" not in os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        and "unity" not in os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    ):
        return None

    return _parse_gnome_version_from_xml() or _parse_gnome_version_from_shell_cmd()


def _parse_gnome_version_from_xml():
    """Try parsing gnome-version xml file."""
    gnome_version = None
    try:
        content = _get_gnome_version_xml()
        if result := re.search(r"(?<=<platform>)\d+(?=<\/platform>)", content):
            platform = int(result[0])
        else:
            raise ValueError
        if result := re.search(r"(?<=<minor>)\d+(?=<\/minor>)", content):
            minor = int(result[0])
        else:
            raise ValueError
        gnome_version = version.parse(f"{platform}.{minor}")
    except Exception as e:  # pylint: disable=broad-except
        logger.warning("Exception when trying to get gnome version from xml %s", e)

    return gnome_version


def _parse_gnome_version_from_shell_cmd():
    """Try parsing gnome-shell output."""
    gnome_version = None
    try:
        output_raw = subprocess.check_output(["gnome-shell", "--version"], shell=False)
        output = output_raw.decode().strip()
        if result := re.search(r"\s+([\d.]+)", output):
            gnome_version = version.parse(result.groups()[0])
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    except Exception as e:  # pylint: disable=broad-except
        logger.warning("Exception when trying to get gnome version from cli %s", e)

    return gnome_version


# pylint: disable=C0415 # Import outside toplevel
def get_appropriate_grab_screens():
    if not _display_manager_is_wayland():
        from normcap.screengrab import qt

        return qt.grab_screens

    gnome_version = get_gnome_version()
    if not gnome_version or gnome_version >= version.parse("41"):
        from normcap.screengrab import dbus_portal

        return dbus_portal.grab_screens

    from normcap.screengrab import dbus_shell

    return dbus_shell.grab_screens
