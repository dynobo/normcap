"""Gather relevant system information."""
import functools
import logging
import os
import sys
from importlib import metadata
from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6 import __version__ as PySide6_version

from normcap import __version__
from normcap.gui.models import DesktopEnvironment, Rect, Screen
from normcap.screengrab.utils import get_gnome_version

logger = logging.getLogger(__name__)


def get_resources_path() -> Path:
    return (Path(__file__).parent.parent / "resources").resolve()


def is_prebuild_package() -> Optional[str]:
    package = sys.modules["__main__"].__package__
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
    XDG_SESSION_TYPE = os.environ.get("XDG_SESSION_TYPE", "").lower()
    WAYLAND_DISPLAY = os.environ.get("WAYLAND_DISPLAY", "").lower()
    return "wayland" in WAYLAND_DISPLAY or "wayland" in XDG_SESSION_TYPE


@functools.cache
def desktop_environment() -> DesktopEnvironment:
    """Detect used desktop environment (Linux)."""
    KDE_FULL_SESSION = os.environ.get("KDE_FULL_SESSION", "").lower()
    XDG_CURRENT_DESKTOP = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    DESKTOP_SESSION = os.environ.get("DESKTOP_SESSION", "").lower()
    GNOME_DESKTOP_SESSION_ID = os.environ.get("GNOME_DESKTOP_SESSION_ID", "")

    if GNOME_DESKTOP_SESSION_ID != "" or "gnome" in XDG_CURRENT_DESKTOP:
        return DesktopEnvironment.GNOME
    if KDE_FULL_SESSION != "" or "kde-plasma" in DESKTOP_SESSION:
        return DesktopEnvironment.KDE
    if "sway" in XDG_CURRENT_DESKTOP:
        return DesktopEnvironment.SWAY

    return DesktopEnvironment.OTHER


def screens() -> dict[int, Screen]:
    """Get informations about available monitors."""
    primary_screen = QtWidgets.QApplication.primaryScreen()
    screens_dict = {}
    for idx, screen in enumerate(QtWidgets.QApplication.screens()):
        is_primary = primary_screen == screen
        device_pixel_ratio = QtGui.QScreen.devicePixelRatio(screen)

        geometry = screen.geometry()
        geometry_rect = Rect(
            top=geometry.top(),
            left=geometry.left(),
            bottom=geometry.top() + geometry.height(),
            right=geometry.left() + geometry.width(),
        )

        screens_dict[idx] = Screen(
            is_primary=is_primary,
            device_pixel_ratio=device_pixel_ratio,
            geometry=geometry_rect,
            index=idx,
        )
    return screens_dict


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


def get_tessdata_path() -> str:
    """Deside which path for tesseract language files to use."""
    prefix = os.environ.get("TESSDATA_PREFIX", None)

    if is_prebuild_package():
        path = config_directory() / "tessdata"
    elif prefix:
        path = Path(prefix) / "tessdata"
    else:
        return ""

    if not path.is_dir():
        raise RuntimeError(f"tessdata directory does not exist: {path}")
    if not list(path.glob("*.traineddata")):
        raise RuntimeError(f"Could not find language data files in {path}")

    return str(path.resolve())


def to_dict() -> dict:
    """Cast all system infos to string for logging."""
    return dict(
        cli_args=" ".join(sys.argv),
        is_prebuild_package=is_prebuild_package(),
        platform=sys.platform,
        pyside6_version=PySide6_version,
        qt_version=QtCore.qVersion(),
        qt_library_path=", ".join(QtCore.QCoreApplication.libraryPaths()),
        config_directory=config_directory(),
        normcap_version=__version__,
        tessdata_path=get_tessdata_path(),
        envs={
            "TESSERACT_CMD": os.environ.get("TESSERACT_CMD", None),
            "TESSERACT_VERSION": os.environ.get("TESSERACT_VERSION", None),
            "TESSDATA_PREFIX": os.environ.get("TESSDATA_PREFIX", None),
            "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH", None),
        },
        desktop_environment=desktop_environment(),
        display_manager_is_wayland=display_manager_is_wayland(),
        gnome_version=get_gnome_version(),
        screens=screens(),
    )
