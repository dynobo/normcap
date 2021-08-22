"""Some utility functions."""

import contextlib
import datetime
import functools
import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional

import importlib_resources
from jeepney.io.blocking import open_dbus_connection  # type: ignore
from jeepney.wrappers import MessageGenerator, new_method_call  # type: ignore
from PySide2 import QtCore, QtGui, QtWidgets

from normcap import system_info
from normcap.data import URLS
from normcap.logger import logger


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


def qt_message_handler(mode, _, message):
    """Intercept QT message.

    Used to hide away unnecessary warnings by showing them only on higher
    log level (--very-verbose).
    """
    level = mode.name.decode("utf8").lower()
    msg = message.lower()
    if (level == "qtfatalmsg") or ("could not load the qt platform" in msg):
        logger.error(f"[QT] {level} - {msg}")
    else:
        logger.debug(f"[QT] {level} - {msg}")

    if ("xcb" in msg) and ("it was found" in msg):
        logger.error(f"Try solving the problem as described here: {URLS.xcb_error}")
        logger.error(f"If that doesn't help, please open an issue: {URLS.issues}")


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


@functools.lru_cache(maxsize=None)
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


def init_tessdata():
    """If packaged, copy language data files to config directory."""
    # if not system_info.is_briefcase_package():
    #    return

    tessdata_path = system_info.config_directory() / "tessdata"
    if len(list(tessdata_path.glob("*.traineddata"))) > 0:
        return

    resource_path = Path(importlib_resources.files("normcap.resources"))
    traineddata_files = list((resource_path / "tessdata").glob("*.traineddata"))
    doc_files = list((resource_path / "tessdata").glob("*.txt"))

    logger.info(f"Copy {len(traineddata_files)} traineddata files to config directory")
    tessdata_path.mkdir(parents=True, exist_ok=True)
    for f in traineddata_files + doc_files:
        shutil.copy(f, tessdata_path / f.name)
