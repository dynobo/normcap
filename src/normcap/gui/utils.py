"""Some utility functions."""

import datetime
import functools
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

from PIL import Image
from PySide6 import QtCore, QtGui, QtWidgets

try:
    from PySide6 import QtDBus

    HAS_QTDBUS = True
except ImportError:
    HAS_QTDBUS = False


from normcap.gui import system_info

logger = logging.getLogger(__name__)


def save_image_in_tempfolder(
    image: Image.Image, postfix: str = "", log_level: int = logging.DEBUG
) -> None:
    """For debugging it can be useful to store the cropped image."""
    if logger.getEffectiveLevel() == log_level:
        file_dir = Path(tempfile.gettempdir()) / "normcap"
        file_dir.mkdir(exist_ok=True)
        now = datetime.datetime.now()
        file_name = f"{now:%Y-%m-%d_%H-%M-%S_%f}{postfix}.png"
        image.save(str(file_dir / file_name))
        logger.debug("Store debug image in: %s", file_dir / file_name)


def move_active_window_to_position_on_gnome(screen_geometry: QtCore.QRect) -> None:
    """Move currently active window to a certain position.

    This is a workaround for not being able to reposition windows on wayland.
    It only works on Gnome Shell.
    """
    if not HAS_QTDBUS:
        raise TypeError("QtDBus should only be called on Linux systems!")

    js_code = f"""
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
    item = "org.gnome.Shell"
    interface = "org.gnome.Shell"
    path = "/org/gnome/Shell"

    bus = QtDBus.QDBusConnection.sessionBus()
    if not bus.isConnected():
        logger.error("Not connected to dbus!")

    shell_interface = QtDBus.QDBusInterface(item, path, interface, bus)
    if shell_interface.isValid():
        x = shell_interface.call("Eval", js_code)
        if x.errorName():
            logger.error("Failed move Window!")
            logger.error(x.errorMessage())
    else:
        logger.warning("Invalid dbus interface on Gnome")


def move_active_window_to_position_on_kde(screen_geometry: QtCore.QRect) -> None:
    """Move currently active window to a certain position.

    This is a workaround for not being able to reposition windows on wayland.
    It only works on KDE.
    """
    if not HAS_QTDBUS:
        raise TypeError("QtDBus should only be called on Linux systems!")

    js_code = f"""
    client = workspace.activeClient;
    client.geometry = {{
        "x": {screen_geometry.left},
        "y": {screen_geometry.top},
        "width": {screen_geometry.width},
        "height": {screen_geometry.height}
    }};
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".js") as script_file:
        script_file.write(js_code.encode())

    bus = QtDBus.QDBusConnection.sessionBus()
    if not bus.isConnected():
        logger.error("Not connected to dbus!")

    item = "org.kde.KWin"
    interface = "org.kde.kwin.Scripting"
    path = "/Scripting"
    shell_interface = QtDBus.QDBusInterface(item, path, interface, bus)

    # FIXME: shell_interface is not valid on latest KDE in Fedora 36.
    if shell_interface.isValid():
        x = shell_interface.call("loadScript", script_file.name)
        y = shell_interface.call("start")
        if x.errorName() or y.errorName():
            logger.error("Failed move Window!")
            logger.error(x.errorMessage(), y.errorMessage())
    else:
        logger.warning("Invalid dbus interface on KDE")

    os.unlink(script_file.name)


def _get_local_icon_path(icon_name: str) -> Optional[Path]:
    """Probe local resource folder for icon file and return it."""
    potential_suffixes = ["", ".svg", ".png"]
    for suffix in potential_suffixes:
        icon_path = system_info.get_resources_path() / (icon_name + suffix)
        if icon_path.exists():
            return icon_path.resolve()
    return None


@functools.cache
def get_icon(icon_name: str) -> QtGui.QIcon:
    """Load icon from system or if not available from resources."""
    if QtGui.QIcon.hasThemeIcon(icon_name):
        return QtGui.QIcon.fromTheme(icon_name)

    if pixmapi := getattr(QtWidgets.QStyle.StandardPixmap, icon_name, None):
        return QtWidgets.QApplication.style().standardIcon(pixmapi)

    if icon_path := _get_local_icon_path(icon_name):
        icon = QtGui.QIcon()
        icon.addFile(str(icon_path))
        return icon

    raise ValueError(f"Could not find icon '{icon_name}'.")


def set_cursor(cursor: Optional[QtCore.Qt.CursorShape] = None) -> None:
    """Show in-progress cursor for application."""
    if cursor is not None:
        QtWidgets.QApplication.setOverrideCursor(cursor)
    else:
        QtWidgets.QApplication.restoreOverrideCursor()
    QtWidgets.QApplication.processEvents()
