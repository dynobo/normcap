"""Some utility functions."""

import logging
import os
import tempfile

try:
    from PySide6 import QtDBus

    HAS_QTDBUS = True
except ImportError:
    HAS_QTDBUS = False


from normcap.gui import models

logger = logging.getLogger(__name__)


def move_active_window_to_position_on_gnome(screen_rect: models.Rect) -> None:
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
                {screen_rect.left},
                {screen_rect.top},
                {screen_rect.width},
                {screen_rect.height}
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


def move_active_window_to_position_on_kde(screen_rect: models.Rect) -> None:
    """Move currently active window to a certain position.

    This is a workaround for not being able to reposition windows on wayland.
    It only works on KDE.
    """
    if not HAS_QTDBUS:
        raise TypeError("QtDBus should only be called on Linux systems!")

    js_code = f"""
    client = workspace.activeClient;
    client.geometry = {{
        "x": {screen_rect.left},
        "y": {screen_rect.top},
        "width": {screen_rect.width},
        "height": {screen_rect.height}
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
