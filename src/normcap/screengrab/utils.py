import ctypes
import ctypes.util
import functools
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from normcap.version import Version

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


def has_wayland_display_manager() -> bool:
    """Identify relevant display managers (Linux)."""
    if sys.platform != "linux":
        return False
    xdg_session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    wayland_display = os.environ.get("WAYLAND_DISPLAY", "").lower()
    return "wayland" in wayland_display or "wayland" in xdg_session_type


def _get_gnome_version_xml() -> str:
    gnome_version_xml = Path("/usr/share/gnome/gnome-version.xml")
    if gnome_version_xml.exists():
        return gnome_version_xml.read_text(encoding="utf-8")

    raise FileNotFoundError


@functools.lru_cache
def get_gnome_version() -> Optional[Version]:
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


def _parse_gnome_version_from_xml() -> Optional[Version]:
    """Try parsing gnome-version xml file."""
    gnome_version = None
    try:
        content = _get_gnome_version_xml()
        if result := re.search(r"(?<=<platform>)\d+(?=<\/platform>)", content):
            platform = int(result[0])
        else:
            raise ValueError("<platform> not found.")
        if result := re.search(r"(?<=<minor>)\d+(?=<\/minor>)", content):
            minor = int(result[0])
        else:
            raise ValueError("<minor> not found.")
        gnome_version = Version(f"{platform}.{minor}")
    except FileNotFoundError:
        logger.debug("Couldn't find from gnome-version.xml")
    except Exception as e:
        logger.warning(
            "Couldn't parse gnome version from gnome-version.xml", exc_info=e
        )

    return gnome_version


def _parse_gnome_version_from_shell_cmd() -> Optional[Version]:
    """Try parsing gnome-shell output."""
    gnome_version = None
    try:
        output_raw = subprocess.check_output(["gnome-shell", "--version"], shell=False)
        output = output_raw.decode().strip()
        if result := re.search(r"\s+([\d.]+)", output):
            gnome_version = Version(result.groups()[0])
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    except Exception as e:
        logger.warning("Exception when trying to get gnome version from cli %s", e)

    return gnome_version


def has_dbus_portal_support() -> bool:
    gnome_version = get_gnome_version()
    return not gnome_version or gnome_version >= Version("41")


def macos_reset_screenshot_permission() -> None:
    """Use tccutil to reset permissions for current application."""
    logger.info("Reset screen recording permissions for eu.dynobo.normcap")
    cmd = ["tccutil", "reset", "ScreenCapture", "eu.dynobo.normcap"]
    try:
        completed_proc = subprocess.run(
            cmd,
            shell=False,
            encoding="utf-8",
            check=False,
            timeout=10,
        )
        if completed_proc.returncode != 0:
            logger.error(
                "Failed resetting screen recording permissions: %s %s",
                completed_proc.stdout,
                completed_proc.stderr,
            )
    except Exception as e:
        logger.error("Couldn't reset screen recording permissions: %s", e)


def has_screenshot_permission() -> bool:
    if sys.platform == "darwin":
        return _macos_has_screenshot_permission()
    if sys.platform == "linux":
        return True
    if sys.platform == "win32":
        return True
    raise RuntimeError("Unknown platform")


def _macos_has_screenshot_permission() -> bool:
    """Use CoreGraphics to check if application has screen recording permissions.

    Returns
    -------
        True if permissions are available or can't be detected.
    """
    try:
        core_graphics = ctypes.util.find_library("CoreGraphics")
        if not core_graphics:
            raise RuntimeError("Couldn't load CoreGraphics")
        cg = ctypes.cdll.LoadLibrary(core_graphics)
        has_permission = bool(cg.CGPreflightScreenCaptureAccess())
    except Exception as e:
        has_permission = True
        logger.warning("Couldn't detect screen recording permission: %s", e)
        logger.warning("Assuming screen recording permission is %s", has_permission)
    return has_permission


def macos_request_screenshot_permission() -> None:
    """Use CoreGraphics to request screen recording permissions."""
    try:
        core_graphics = ctypes.util.find_library("CoreGraphics")
        if not core_graphics:
            raise ValueError("Couldn' find CoreGraphics")
        cg = ctypes.cdll.LoadLibrary(core_graphics)
        logger.debug("Request screen recording access")
        cg.CGRequestScreenCaptureAccess()
    except Exception as e:
        logger.warning("Couldn't request screen recording permission: %s", e)


def macos_open_privacy_settings() -> None:
    link_to_preferences = (
        "x-apple.systempreferences:com.apple.preference.security"
        + "?Privacy_ScreenCapture"
    )
    try:
        if sys.platform != "darwin":
            raise RuntimeError(f"Tried opening macOS settings on {sys.platform}")
        subprocess.run(
            ["open", link_to_preferences],
            shell=False,
            check=True,
            timeout=30,
        )
    except Exception as e:
        logger.error("Couldn't open privacy settings: %s", e)
