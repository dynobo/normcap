"""Gather relevant system information."""
import functools
import logging
import os
import sys
from importlib import metadata
from pathlib import Path
from typing import Optional

from normcap import __version__
from normcap.gui.models import DesktopEnvironment, Rect, Screen
from normcap.screengrab.utils import get_gnome_version
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6 import __version__ as pyside_version


logger = logging.getLogger(__name__)


def get_resources_path() -> Path:
    return (Path(__file__).parent.parent / "resources").resolve()


def is_flatpak_package() -> bool:
    return os.getenv("FLATPAK_ID") is not None


def get_prebuild_package_type() -> Optional[str]:
    # sourcery skip: assign-if-exp, reintroduce-else
    package = getattr(sys.modules["__main__"], "__package__", None)
    if package and "Briefcase-Version" in metadata.metadata(package):
        # Briefcase package
        return "briefcase"

    if hasattr(sys.modules["__main__"], "__compiled__"):
        # Nuitka package
        return "nuitka"

    return None


@functools.cache
def display_manager_is_wayland() -> bool:
    """Identify relevant display managers (Linux)."""
    xdg_session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    wayland_display = os.environ.get("WAYLAND_DISPLAY", "").lower()
    return "wayland" in wayland_display or "wayland" in xdg_session_type


@functools.cache
def desktop_environment() -> DesktopEnvironment:
    """Detect used desktop environment (Linux)."""
    kde_full_session = os.environ.get("KDE_FULL_SESSION", "").lower()
    xdg_current_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    desktop_session = os.environ.get("DESKTOP_SESSION", "").lower()
    gnome_desktop_session_id = os.environ.get("GNOME_DESKTOP_SESSION_ID", "")
    if gnome_desktop_session_id == "this-is-deprecated":
        gnome_desktop_session_id = ""

    if gnome_desktop_session_id != "" or "gnome" in xdg_current_desktop:
        return DesktopEnvironment.GNOME
    if kde_full_session != "" or "kde-plasma" in desktop_session:
        return DesktopEnvironment.KDE
    if "sway" in xdg_current_desktop:
        return DesktopEnvironment.SWAY
    if "unity" in xdg_current_desktop:
        return DesktopEnvironment.UNITY

    return DesktopEnvironment.OTHER


def screens() -> dict[int, Screen]:
    """Get informations about available monitors."""
    # TODO: Refactor into simple list, idx is not necessary
    return {
        idx: Screen(
            is_primary=screen == QtWidgets.QApplication.primaryScreen(),
            device_pixel_ratio=QtGui.QScreen.devicePixelRatio(screen),
            geometry=Rect(*screen.geometry().getRect()),
            index=idx,
        )
        for idx, screen in enumerate(QtWidgets.QApplication.screens())
    }


def config_directory() -> Path:
    """Retrieve platform specific configuration directory."""
    postfix = "normcap"

    # Windows
    if sys.platform == "win32":
        if local_appdata := os.getenv("LOCALAPPDATA"):
            return Path(local_appdata) / postfix
        if appdata := os.getenv("APPDATA"):
            return Path(appdata) / postfix
        raise ValueError("Could not determine the appdata directory.")

    # Linux and Mac
    if xdg_config_home := os.getenv("XDG_CONFIG_HOME"):
        return Path(xdg_config_home) / postfix

    return Path.home() / ".config" / postfix


def get_tessdata_path() -> Optional[os.PathLike]:
    """Deside which path for tesseract language files to use."""
    prefix = os.environ.get("TESSDATA_PREFIX", None)

    if get_prebuild_package_type() or is_flatpak_package():
        path = config_directory() / "tessdata"
    elif prefix:
        path = Path(prefix) / "tessdata"
    else:
        return None

    if not path.is_dir():
        raise RuntimeError(f"tessdata directory does not exist: {path}")
    if not list(path.glob("*.traineddata")):
        raise RuntimeError(f"Could not find language data files in {path}")

    return path.resolve()


def to_dict() -> dict:
    """Cast all system infos to string for logging."""
    return {
        "cli_args": " ".join(sys.argv),
        "is_prebuild_package": get_prebuild_package_type(),
        "is_flatpak_package": is_flatpak_package(),
        "platform": sys.platform,
        "pyside6_version": pyside_version,
        "qt_version": QtCore.qVersion(),
        "qt_library_path": ", ".join(QtCore.QCoreApplication.libraryPaths()),
        "config_directory": config_directory(),
        "normcap_version": __version__,
        "tessdata_path": get_tessdata_path(),
        "envs": {
            "TESSERACT_CMD": os.environ.get("TESSERACT_CMD", None),
            "TESSERACT_VERSION": os.environ.get("TESSERACT_VERSION", None),
            "TESSDATA_PREFIX": os.environ.get("TESSDATA_PREFIX", None),
            "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH", None),
        },
        "desktop_environment": desktop_environment(),
        "display_manager_is_wayland": display_manager_is_wayland(),
        "gnome_version": get_gnome_version(),
        "screens": screens(),
    }
