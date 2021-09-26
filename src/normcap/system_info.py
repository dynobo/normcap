"""Gather relevant system information."""
import functools
import os
import pprint
import sys
import traceback
from pathlib import Path
from typing import Dict

import importlib_metadata
import PySide2
import tesserocr  # type: ignore
from PySide2 import QtGui, QtWidgets

from normcap import __version__
from normcap.data import FILE_ISSUE_TEXT
from normcap.models import (
    DesktopEnvironment,
    DisplayManager,
    Rect,
    ScreenInfo,
    TesseractInfo,
)


def display_manager() -> DisplayManager:
    """Identify relevant display managers (Linux)."""
    XDG_SESSION_TYPE = os.environ.get("XDG_SESSION_TYPE", "").lower()
    WAYLAND_DISPLAY = os.environ.get("WAYLAND_DISPLAY", "").lower()
    if "wayland" in WAYLAND_DISPLAY or "wayland" in XDG_SESSION_TYPE:
        return DisplayManager.WAYLAND
    if "x11" in XDG_SESSION_TYPE:
        return DisplayManager.X11
    return DisplayManager.OTHER


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


@functools.lru_cache(maxsize=None)
def screens() -> Dict[int, ScreenInfo]:
    """Get informations about available monitors."""
    primary_screen = QtWidgets.QApplication.primaryScreen()
    screens_dict = {}
    for idx, screen in enumerate(QtWidgets.QApplication.screens()):
        is_primary = primary_screen == screen
        device_pixel_ratio = QtGui.QScreen.devicePixelRatio(screen)

        geometry = QtGui.QScreen.geometry(screen)

        geometry_rect = Rect(
            top=geometry.top(),
            left=geometry.left(),
            bottom=geometry.top() + geometry.height(),
            right=geometry.left() + geometry.width(),
        )

        screens_dict[idx] = ScreenInfo(
            is_primary=is_primary,
            device_pixel_ratio=device_pixel_ratio,
            geometry=geometry_rect,
            index=idx,
        )
    return screens_dict


def primary_screen_idx() -> int:
    """Get index from primary monitor."""
    for idx, screen in screens().items():
        if screen.is_primary:
            return idx
    raise ValueError("Unable to detect primary screen")


@functools.lru_cache(maxsize=None)
def tesseract() -> TesseractInfo:
    """Get info abput tesseract setup."""
    kwargs = {}
    if is_briefcase_package():
        kwargs["path"] = _get_tessdata_config_path()

    try:
        with tesserocr.PyTessBaseAPI(**kwargs) as api:
            languages = sorted(api.GetAvailableLanguages())
            version = api.Version()
            tessdata = api.GetDatapath()
    except RuntimeError as e:
        traceback.print_tb(e.__traceback__)
        raise RuntimeError(
            "Couldn't determine Tesseract information. If you pip installed NormCap "
            + "make sure Tesseract is installed and configured correctly. Otherwise: "
            + FILE_ISSUE_TEXT
        ) from e

    if not languages:
        raise ValueError(
            "Could not load any languages for tesseract. "
            + "On Windows, make sure that TESSDATA_PREFIX environment variable is set. "
            + "On Linux/MacOS see if 'tesseract --list-langs' work is the command line."
        )

    return TesseractInfo(version=version, languages=languages, path=tessdata)


def _get_tessdata_config_path() -> str:
    """Deside which path for tesseract language files to use."""
    path = config_directory() / "tessdata"

    if not path.is_dir():
        raise RuntimeError(f"tessdata directory does not exist: {path}")
    if len(list(path.glob("*.traineddata"))) < 1:
        raise RuntimeError(f"Could not find language data files in {path}")

    path_str = str(path.absolute())
    if not path_str.endswith(os.sep):
        path_str += os.sep

    return path_str


def is_briefcase_package() -> bool:
    """Check if script is executed in briefcase package."""
    app_module = sys.modules["__main__"].__package__
    metadata = importlib_metadata.metadata(app_module)
    return "Briefcase-Version" in metadata


def config_directory() -> Path:
    """Retrieve platform specific configuration directory."""
    postfix = "normcap"

    # Windows
    if sys.platform == "win32":
        local_appdata = os.getenv("LOCALAPPDATA")
        if local_appdata:
            return Path(local_appdata) / postfix
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / postfix
        raise ValueError("Couldn't determine the appdata directory.")

    # Linux and Mac
    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / postfix
    return Path.home() / ".config" / postfix


def to_string() -> str:
    """Cast all system infos to string for logging."""
    return pprint.pformat(
        dict(
            is_briefcase_package=is_briefcase_package(),
            platform=sys.platform,
            pyside2_version=PySide2.__version__,
            qt_version=PySide2.QtCore.__version__,
            config_directory=config_directory(),
            normcap_version=__version__,
            tesseract_version=tesseract().version,
            tesseract_languages=tesseract().languages,
            tessdata_path=tesseract().path,
            desktop_environment=desktop_environment(),
            display_manager=display_manager(),
            screens=screens(),
        ),
        indent=3,
    )
