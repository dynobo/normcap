"""Some utility functions."""

import contextlib
import datetime
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import importlib_metadata
import importlib_resources
import tesserocr  # type: ignore  # pylint: disable=wrong-import-order
from jeepney.io.blocking import open_dbus_connection  # type: ignore
from jeepney.wrappers import MessageGenerator, new_method_call  # type: ignore
from PySide2 import QtCore, QtGui, QtWidgets

from normcap import __version__
from normcap.logger import logger
from normcap.models import (
    URLS,
    DesktopEnvironment,
    DisplayManager,
    Platform,
    Rect,
    ScreenInfo,
    SystemInfo,
)


def save_image_in_tempfolder(
    image: QtGui.QImage, postfix: str = "", log_level=logging.DEBUG
):
    """For debugging it can be useful to store the cropped image."""
    if logger.level == log_level:
        file_dir = Path(tempfile.gettempdir()) / "normcap"
        file_dir.mkdir(exist_ok=True)
        now = datetime.datetime.now()
        file_name = f"{now:%Y-%m-%d_%H-%M-%S_%f}{postfix}.png"
        image.save(str(file_dir / file_name))
        logger.debug(f"Debug image stored in: {file_dir / file_name}")


def get_screen_idx_of_mouse() -> QtCore.QRect:
    """Detect screen index of display with mouse pointer."""
    desktop = QtWidgets.QApplication.desktop()
    mouse_screen = desktop.screenNumber(QtGui.QCursor.pos())
    return mouse_screen


def get_platform() -> Platform:
    """Retrieve platform information."""
    platform_str = sys.platform.lower()
    if platform_str.startswith("linux"):
        return Platform.LINUX
    if platform_str.startswith("win"):
        return Platform.WINDOWS
    if platform_str.startswith("darwin"):
        return Platform.MACOS

    raise ValueError(f"Unknown system platform: {platform_str}")


def get_display_manager() -> DisplayManager:
    """Identify relevant display managers (Linux)."""
    XDG_SESSION_TYPE = os.environ.get("XDG_SESSION_TYPE", "").lower()
    WAYLAND_DISPLAY = os.environ.get("WAYLAND_DISPLAY", "").lower()
    if "wayland" in WAYLAND_DISPLAY or "wayland" in XDG_SESSION_TYPE:
        return DisplayManager.WAYLAND
    if "x11" in XDG_SESSION_TYPE:
        return DisplayManager.X11

    return DisplayManager.OTHER


def get_desktop_environment() -> DesktopEnvironment:
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


def get_screen_infos() -> Dict[int, ScreenInfo]:
    """Get informations about available monitors."""
    primary_screen = QtWidgets.QApplication.primaryScreen()
    screens = {}
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

        screens[idx] = ScreenInfo(
            is_primary=is_primary,
            device_pixel_ratio=device_pixel_ratio,
            geometry=geometry_rect,
            index=idx,
        )
    return screens


def get_tesseract_version() -> str:
    """Determine tesseract version."""

    tesseract_version = "unknown"
    try:
        lines = tesserocr.tesseract_version().strip().split()
        tesseract_version = lines[1]
    except RuntimeError as e:
        raise RuntimeError(
            "Couldn't determine Tesseract version number. You might "
            + "have to put the directory of the tesseract executable into your systems "
            + "PATH environment variable."
        ) from e
    return tesseract_version


def is_briefcase_package() -> bool:
    """Check if script is executed in briefcase package."""

    app_module = sys.modules["__main__"].__package__
    metadata = importlib_metadata.metadata(app_module)
    return "Briefcase-Version" in metadata


def get_tessdata_path() -> str:
    """Deside which path for tesseract language files to use."""
    resource_path = Path(importlib_resources.files("normcap.resources"))

    path = None

    # Use path set via env var, if it exists
    if "TESSDATA_PREFIX" in os.environ:
        path = Path(os.environ["TESSDATA_PREFIX"])

    if is_briefcase_package():
        path = resource_path

    # TODO: Also look into
    # /usr/share/tesseract-ocr/4.00/tessdata
    # /usr/share/tessdata
    # /usr/local/share/tessdata
    # Windows?
    # MacOS?

    if path and path.is_dir():
        return str(path.absolute()) + os.sep + "tessdata" + os.sep

    # TODO: Doesn't seem right
    if path is None:
        return ""

    raise ValueError(f"No valid path for tessdata found. {path} is invalid")


def get_tesseract_languages() -> List[str]:
    """Detect available tesseract languages."""

    path = get_tessdata_path()
    logger.info(f"Searching tesseract languages {path}")
    tesseract_languages = list(tesserocr.get_languages(path=path)[1])

    if len(tesseract_languages) < 1:
        raise ValueError(
            "Could load any languages for tesseract. "
            + "On Windows, make sure that TESSDATA_PREFIX environment variable is set. "
            + "On Linux/MacOS see if 'tesseract --list-langs' work is the command line."
        )

    return tesseract_languages


def get_system_info() -> SystemInfo:
    """Gather relevant system information."""

    return SystemInfo(
        platform=get_platform(),
        display_manager=get_display_manager(),
        desktop_environment=get_desktop_environment(),
        normcap_version=__version__,
        tesseract_version=get_tesseract_version(),
        tesseract_languages=get_tesseract_languages(),
        tessdata_path=get_tessdata_path(),
        briefcase_package=is_briefcase_package(),
        screens=get_screen_infos(),
    )


def qt_message_handler(mode, _, msg):
    """Intercept QT message.

    Used to hide away unnecessary warnings by showing them only on higher
    log level (--very-verbose).
    """
    level = mode.name.decode("utf8")

    if level.lower() == "qtfatalmsg":
        logger.error(f"[QT] {level} - {msg}")
    elif "could not load the qt platform" in msg.lower():
        logger.error(f"[QT] {level} - {msg}")
        if "xcb" in msg.lower() and "it was found" + URLS.faqs in msg.lower():
            logger.error(f"Try solving the problem as described here: {URLS.xcb_error}")
            logger.error(f"If that doesn't help, please open an issue: {URLS.issues}")
    else:
        logger.debug(f"[QT] {level} - {msg}")


@contextlib.contextmanager
def temporary_environ(**modify_vars):
    """Temporarily adjust environment variables."""
    modify_vars = {k: str(v) for k, v in modify_vars.items()}
    env = os.environ
    vars_before = {k: dict(env).get(k, "NOT_EXISTING") for k in modify_vars}
    try:
        if len(modify_vars) > 0:
            env.update(modify_vars)
        yield
    finally:
        env.update(vars_before)
        for var_name, var_value in vars_before.items():
            if var_value == "NOT_EXISTING":
                env.pop(var_name, default=None)


def move_active_window_to_position_on_gnome(screen_geometry):
    """Move currently active window to a certain position.

    This is a workaround for not being able to reposition windows on wayland.
    It only works on Gnome Shell.
    """
    JS_CODE = f"""
    const GLib = imports.gi.GLib;
    global.get_window_actors().forEach(function (w) {{
        var mw = w.meta_window;
        if (mw.has_focus()) {{
            mw.move_resize_frame(
                0,
                {screen_geometry.left},
                {screen_geometry.top},
                {screen_geometry.width},
                {screen_geometry.height}
            );
        }}
    }});
    """

    class MoveWindow(MessageGenerator):
        """Move window through dbus."""

        interface = "org.gnome.Shell"

        def __init__(self):
            """Init jeepney message generator."""
            super().__init__(
                object_path="/org/gnome/Shell",
                bus_name="org.gnome.Shell",
            )

        def move(self):
            """Grab specific section to file with flash disabled."""
            return new_method_call(self, "Eval", "s", (JS_CODE,))

    connection = open_dbus_connection(bus="SESSION")
    msg = MoveWindow().move()
    _ = connection.send_and_get_reply(msg)


def except_hook(cls, exception, traceback):
    """Print traceback and quit application."""
    logger.error(
        "Uncaught exception! Quitting NormCap!", exc_info=(cls, exception, traceback)
    )
    sys.exit(1)


def get_icon(icon_file: str, system_icon: Optional[str] = None) -> QtGui.QIcon:
    """Load icon from system or if not available from resources."""
    icon = None
    if system_icon:
        icon = QtGui.QIcon.fromTheme(system_icon)
    if not icon:
        with importlib_resources.path("normcap.resources", icon_file) as fp:
            icon_path = str(fp.absolute())
        icon = QtGui.QIcon()
        icon.addFile(icon_path)
    return icon


def set_cursor(cursor: Optional[QtCore.Qt.CursorShape] = None):
    """Show in-progress cursor for application.

    QtCore.Qt.WaitCursor
    QtCore.Qt.CrossCursor
    QtCore.Qt.ArrowCursor
    """
    if cursor is not None:
        QtWidgets.QApplication.setOverrideCursor(cursor)
    else:
        QtWidgets.QApplication.restoreOverrideCursor()
    QtWidgets.QApplication.processEvents()


def get_config_directory() -> Path:
    """Retrieve platform specific configuration directory.

    DEPRECATED! TODO: Remove in later point of time
    """
    platform_str = sys.platform.lower()

    # Windows
    if platform_str == "win":
        local_appdata = os.getenv("LOCALAPPDATA")
        if local_appdata:
            return Path(local_appdata)
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata)
        raise ValueError("Couldn't determine the appdata directory.")

    # Linux and Mac
    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home)
    return Path.home() / ".config"
