from packaging import version
from PySide6 import QtGui

from normcap.screengrab import dbus_portal, dbus_shell, qt
from normcap.screengrab.utils import display_manager_is_wayland, gnome_shell_version


def grab_screens() -> list[QtGui.QImage]:
    """Grab screenshot of supplied region."""
    if not display_manager_is_wayland():
        return qt.grab_screens()

    if shell_version := gnome_shell_version():
        if shell_version >= version.parse("41"):
            return dbus_portal.grab_screens()

    return dbus_shell.grab_screens()
