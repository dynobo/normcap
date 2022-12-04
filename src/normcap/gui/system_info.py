"""Gather relevant system information."""
import functools
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6 import __version__ as pyside_version

from normcap import __version__
from normcap.gui.models import DesktopEnvironment, Rect, Screen
from normcap.screengrab.utils import get_gnome_version

logger = logging.getLogger(__name__)


def _get_app_path() -> Path:
    """Base path of briefcase package.

    This is the directory ./app inside the appimage.
    """
    return (Path(__file__).parent.parent.parent).resolve()


def get_resources_path() -> Path:
    return _get_app_path() / "app" / "normcap" / "resources"


def is_briefcase_package() -> bool:
    return (
        _get_app_path().is_dir() and (_get_app_path().parent / "app_packages").is_dir()
    )


@functools.cache
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


@functools.cache
def get_tesseract_path() -> Path:
    if is_briefcase_package():
        bin_path = _get_app_path().parent / "bin"
        extension = ".exe" if sys.platform == "win32" else ""
        tesseract_path = bin_path / f"tesseract{extension}"
        if not tesseract_path.exists():
            raise RuntimeError(f"Couldn't locate tesseract binary in {tesseract_path}!")
        return tesseract_path

    # Then try to find tesseract on system
    if tesseract_path := shutil.which("tesseract"):
        return tesseract_path

    raise RuntimeError(
        "No Tesseract binary found! Tesseract has to be installed and added "
        + "to PATH environment variable."
    )


def _copy_traineddata_files(tessdata_path: Path) -> None:
    logger.info("Copy traineddata files to config directory")
    if is_flatpak_package():
        src_path = Path("/app/share/tessdata")
    else:
        src_path = _get_app_path() / "tessdata"

    # TODO: Remove logging
    logger.debug("Sourcepath: %s", src_path)
    logger.debug("Targetpath: %s", tessdata_path)
    tessdata_path.mkdir(parents=True, exist_ok=True)
    for f in src_path.glob("*.*"):
        logger.debug("Copying: %s", f)
        shutil.copy(f, tessdata_path / f.name)


def get_tessdata_path() -> Optional[os.PathLike]:
    """Deside which path for tesseract language files to use."""
    if is_briefcase_package() or is_flatpak_package():
        tessdata_path = config_directory() / "tessdata"
        if not tessdata_path.is_dir() or not list(tessdata_path.glob("*.traineddata")):
            _copy_traineddata_files(tessdata_path)
        return tessdata_path.resolve()

    if prefix := os.environ.get("TESSDATA_PREFIX", None):
        tessdata_path = Path(prefix) / "tessdata"
        if tessdata_path.is_dir() and list(tessdata_path.glob("*.traineddata")):
            return tessdata_path.resolve()

    logger.warning("No tessdata directory found.")
    return None


def is_flatpak_package() -> bool:
    return os.getenv("FLATPAK_ID") is not None


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


def screens() -> list[Screen]:
    """Get informations about available monitors."""
    return [
        Screen(
            is_primary=screen == QtWidgets.QApplication.primaryScreen(),
            device_pixel_ratio=QtGui.QScreen.devicePixelRatio(screen),
            geometry=Rect(*screen.geometry().getRect()),
            index=idx,
        )
        for idx, screen in enumerate(QtWidgets.QApplication.screens())
    ]


def to_dict() -> dict:
    """Cast all system infos to string for logging."""
    return {
        "cli_args": " ".join(sys.argv),
        "is_briefcase_package": is_briefcase_package(),
        "is_flatpak_package": is_flatpak_package(),
        "platform": sys.platform,
        "pyside6_version": pyside_version,
        "qt_version": QtCore.qVersion(),
        "qt_library_path": ", ".join(QtCore.QCoreApplication.libraryPaths()),
        "config_directory": config_directory(),
        "normcap_version": __version__,
        "tesseract_path": get_tesseract_path(),
        "tessdata_path": get_tessdata_path(),
        "envs": {
            "TESSDATA_PREFIX": os.environ.get("TESSDATA_PREFIX", None),
            "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH", None),
        },
        "desktop_environment": desktop_environment(),
        "display_manager_is_wayland": display_manager_is_wayland(),
        "gnome_version": get_gnome_version(),
        "screens": screens(),
    }
