from packaging import version

from normcap.screengrab.utils import display_manager_is_wayland, get_gnome_version


# pylint: disable=C0415 # Import outside toplevel
def _get_appropriate_grab_screens():
    gnome_version = get_gnome_version()
    is_wayland = display_manager_is_wayland()

    if is_wayland and gnome_version < version.parse("41"):
        from normcap.screengrab import dbus_shell

        return dbus_shell.grab_screens

    if is_wayland:
        from normcap.screengrab import dbus_portal

        return dbus_portal.grab_screens

    from normcap.screengrab import qt

    return qt.grab_screens


grab_screens = _get_appropriate_grab_screens()
