"""Gather relevant system information."""

import functools
import logging
import os
import shutil
import sys
from pathlib import Path
from platform import python_version
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6 import __version__ as pyside_version

from normcap import __version__
from normcap.gui.localization import translate
from normcap.gui.models import DesktopEnvironment, Screen

logger = logging.getLogger(__name__)


@functools.cache
def config_directory() -> Path:
    """Retrieve platform specific configuration directory."""
    postfix = "normcap"

    # Windows
    if sys.platform == "win32":
        if is_portable_windows_package():
            data_path = get_package_root() / "data"
            data_path.mkdir(exist_ok=True)
            return data_path
        if local_appdata := os.getenv("LOCALAPPDATA"):
            return Path(local_appdata) / postfix
        if appdata := os.getenv("APPDATA"):
            return Path(appdata) / postfix
        raise ValueError("Could not determine the appdata directory.")

    # Linux and Mac
    if xdg_config_home := os.getenv("XDG_CONFIG_HOME"):
        return Path(xdg_config_home) / postfix

    return Path.home() / ".config" / postfix


def desktop_dir() -> Path:
    """Return path the User's Desktop directory.

    Raises:
        NotImplementedError: When called on other systems than Windows.

    Returns:
        Path to desktop directory.
    """
    if sys.platform != "win32":
        raise NotImplementedError()

    try:
        import winreg

        reg_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
        )
        desktop = Path(winreg.QueryValueEx(reg_key, "Desktop")[0]).resolve()
        winreg.CloseKey(reg_key)
    except Exception:
        desktop = Path().home() / "Desktop"

    if not desktop.is_dir() or not desktop.exists():
        raise RuntimeError(f"Detected desktop directory '{desktop}' does not exist!")

    return desktop


def get_resources_path() -> Path:
    return Path(__file__).resolve().parents[1] / "resources"


def get_package_root() -> Path:
    return Path(__file__).resolve().parents[3]


@functools.cache
def is_portable_windows_package() -> bool:
    if sys.platform != "win32":
        return False
    portable_file = get_package_root() / "portable"
    return portable_file.is_file()


def is_briefcase_package() -> bool:
    app_path = Path(__file__).resolve().parents[2]
    return app_path.is_dir() and (app_path.parent / "app_packages").is_dir()


def is_appimage_package() -> bool:
    return os.getenv("APPIMAGE") is not None


def is_flatpak_package() -> bool:
    return os.getenv("FLATPAK_ID") is not None


def is_prebuilt_package() -> bool:
    # TODO: Fix usage of this function and rename!
    return is_briefcase_package() or is_flatpak_package()


@functools.cache
def display_manager_is_wayland() -> bool:
    xdg_session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    has_wayland_display_env = bool(os.environ.get("WAYLAND_DISPLAY", ""))
    return "wayland" in xdg_session_type or has_wayland_display_env


@functools.cache
def desktop_environment() -> DesktopEnvironment:  # noqa: PLR0911 # too many returns
    """Detect used desktop environment (Linux)."""
    kde_full_session = os.environ.get("KDE_FULL_SESSION", "").lower()
    xdg_current_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    desktop_session = os.environ.get("DESKTOP_SESSION", "").lower()
    gnome_desktop_session_id = os.environ.get("GNOME_DESKTOP_SESSION_ID", "")
    hyprland_instance_signature = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")

    if gnome_desktop_session_id == "this-is-deprecated":
        gnome_desktop_session_id = ""

    if gnome_desktop_session_id or "gnome" in xdg_current_desktop:
        return DesktopEnvironment.GNOME
    if kde_full_session or "kde-plasma" in desktop_session:
        return DesktopEnvironment.KDE
    if "sway" in xdg_current_desktop or "sway" in desktop_session:
        return DesktopEnvironment.SWAY
    if "unity" in xdg_current_desktop:
        return DesktopEnvironment.UNITY
    if hyprland_instance_signature:
        return DesktopEnvironment.HYPRLAND
    if "awesome" in xdg_current_desktop:
        return DesktopEnvironment.AWESOME

    return DesktopEnvironment.OTHER


def screens() -> list[Screen]:
    """Get information about available monitors."""
    return [
        Screen(
            device_pixel_ratio=QtGui.QScreen.devicePixelRatio(screen),
            left=screen.geometry().left(),
            top=screen.geometry().top(),
            right=screen.geometry().right(),
            bottom=screen.geometry().bottom(),
            index=idx,
        )
        for idx, screen in enumerate(QtWidgets.QApplication.screens())
    ]


@functools.cache
def get_tesseract_bin_path(is_briefcase_package: bool) -> Path:
    """Get the path to the Tesseract binary.

    Returns:
        Path: The path to the Tesseract binary.

    Raises:
        ValueError: If the platform is not supported.
        RuntimeError: If the Tesseract binary cannot be located.
    """
    if is_briefcase_package:
        if sys.platform == "linux" or "bsd" in sys.platform:
            bin_path = Path(__file__).resolve().parents[4] / "bin"
        elif sys.platform == "win32":
            bin_path = Path(__file__).resolve().parents[2] / "resources" / "tesseract"
        elif sys.platform == "darwin":
            bin_path = Path(__file__).resolve().parents[4] / "app_packages" / "bin"
        else:
            raise ValueError(f"Platform {sys.platform} is not supported")
        extension = ".exe" if sys.platform == "win32" else ""
        tesseract_path = bin_path / f"tesseract{extension}"
        if not tesseract_path.exists():
            raise RuntimeError(f"Could not locate Tesseract binary {tesseract_path}!")
        return tesseract_path

    # Then try to find tesseract on system
    if tesseract_bin := shutil.which("tesseract"):
        tesseract_path = Path(tesseract_bin)
        if tesseract_path.exists():
            return tesseract_path

    raise RuntimeError(
        "No Tesseract binary found! Tesseract has to be installed and added "
        "to PATH environment variable."
    )


def get_tessdata_path(
    config_directory: Path, is_briefcase_package: bool, is_flatpak_package: bool
) -> Optional[Path]:
    """Decide which path for tesseract language files to use."""
    if is_briefcase_package or is_flatpak_package:
        tessdata_path = config_directory / "tessdata"
        return tessdata_path.resolve()

    if prefix := os.environ.get("TESSDATA_PREFIX", None):
        tessdata_path = Path(prefix) / "tessdata"
        if tessdata_path.is_dir() and list(tessdata_path.glob("*.traineddata")):
            return tessdata_path.resolve()

    if sys.platform == "win32":
        logger.warning("Missing tessdata directory. (Is TESSDATA_PREFIX variable set?)")

    return None


def to_dict() -> dict:
    """Cast all system infos to string for logging."""
    return {
        "normcap_version": __version__,
        "python_version": python_version(),
        "cli_args": " ".join(sys.argv),
        "is_briefcase_package": is_briefcase_package(),
        "is_flatpak_package": is_flatpak_package(),
        "is_appimage_package": is_appimage_package(),
        "platform": sys.platform,
        "desktop_environment": desktop_environment(),
        "display_manager_is_wayland": display_manager_is_wayland(),
        "pyside6_version": pyside_version,
        "qt_version": QtCore.qVersion(),
        "qt_library_path": ", ".join(QtCore.QCoreApplication.libraryPaths()),
        "locale": translate.info().get("language", "DEFAULT"),
        "config_directory": config_directory(),
        "resources_path": get_resources_path(),
        "tesseract_path": get_tesseract_bin_path(
            is_briefcase_package=is_briefcase_package()
        ),
        "tessdata_path": get_tessdata_path(
            config_directory=config_directory(),
            is_briefcase_package=is_briefcase_package(),
            is_flatpak_package=is_flatpak_package(),
        ),
        "envs": {
            "TESSDATA_PREFIX": os.environ.get("TESSDATA_PREFIX", None),
            "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH", None),
        },
        "screens": screens(),
    }
