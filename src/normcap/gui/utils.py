"""Some utility functions."""

import datetime
import functools
import logging
import shutil
import sys
import tempfile
from importlib import resources
from pathlib import Path
from typing import Optional

from jeepney.io.blocking import open_dbus_connection  # type: ignore
from jeepney.wrappers import MessageGenerator, new_method_call  # type: ignore
from PySide6 import QtCore, QtGui, QtWidgets

from normcap import system_info
from normcap.constants import URLS

logger = logging.getLogger(__name__)


def save_image_in_tempfolder(
    image: QtGui.QImage, postfix: str = "", log_level=logging.DEBUG
):
    """For debugging it can be useful to store the cropped image."""
    if logger.root.level == log_level:
        file_dir = Path(tempfile.gettempdir()) / "normcap"
        file_dir.mkdir(exist_ok=True)
        now = datetime.datetime.now()
        file_name = f"{now:%Y-%m-%d_%H-%M-%S_%f}{postfix}.png"
        image.save(str(file_dir / file_name))
        logger.debug("Store debug image in: %s", file_dir / file_name)


def qt_log_wrapper(mode, _, message):
    """Intercept QT message.

    Used to hide away unnecessary warnings by showing them only on higher
    log level (--very-verbose).
    """
    level = mode.name.decode("utf8").lower()
    msg = message.lower()
    if (level == "qtfatalmsg") or ("could not load the qt platform" in msg):
        logger.error("[QT] %s - %s", level, msg)
    else:
        logger.debug("[QT] %s - %s", level, msg)

    if ("xcb" in msg) and ("it was found" in msg):
        logger.error("Try solving the problem as described here: %s", URLS.xcb_error)
        logger.error("If that doesn't help, please open an issue: %s", URLS.issues)


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


def hook_exceptions(cls, exception, traceback):
    """Print traceback and quit application."""
    logger.error(
        "Uncaught exception! Quitting NormCap!", exc_info=(cls, exception, traceback)
    )
    logger.error("Please open an issue with the output above on %s", URLS.issues)
    sys.exit(1)


@functools.lru_cache(maxsize=None)
def get_icon(icon_file: str, system_icon: Optional[str] = None) -> QtGui.QIcon:
    """Load icon from system or if not available from resources."""
    if system_icon:
        return QtGui.QIcon.fromTheme(system_icon)

    icon = QtGui.QIcon()
    with resources.path("normcap.resources", icon_file) as icon_path:
        icon.addFile(str(icon_path.absolute()))

    return icon


def set_cursor(cursor: Optional[QtCore.Qt.CursorShape] = None):
    """Show in-progress cursor for application."""
    if cursor is not None:
        QtWidgets.QApplication.setOverrideCursor(cursor)
    else:
        QtWidgets.QApplication.restoreOverrideCursor()
    QtWidgets.QApplication.processEvents()


def copy_tessdata_files_to_config_dir():
    """If packaged, copy language data files to config directory."""
    tessdata_path = system_info.config_directory() / "tessdata"
    if list(tessdata_path.glob("*.traineddata")):
        return

    resource_path = Path(resources.files("normcap.resources"))
    traineddata_files = list((resource_path / "tessdata").glob("*.traineddata"))
    doc_files = list((resource_path / "tessdata").glob("*.txt"))

    logger.info("Copy %s traineddata files to config directory", len(traineddata_files))
    tessdata_path.mkdir(parents=True, exist_ok=True)
    for f in traineddata_files + doc_files:
        shutil.copy(f, tessdata_path / f.name)


def copy_to_clipboard():
    """Initialize a wrapper around qt clipboard.

    Necesessary to avoid some wired results on Wayland, where text sometimes get
    copied, and sometimes not.
    """
    # TODO: Test if workaround still necessary with Qt6
    from PySide6 import QtWidgets  # pylint: disable=all

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication()

    def copy_qt(text):
        logger.debug("Copy to clipboard:\n%s", text)
        cb = app.clipboard()
        cb.setText(text)

    return copy_qt
