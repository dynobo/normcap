from packaging import version

from normcap.screengrab.utils import display_manager_is_wayland, gnome_shell_version

if not display_manager_is_wayland():
    from normcap.screengrab import qt

    grab_screens = qt.grab_screens
elif gnome_shell_version() and gnome_shell_version() < version.parse("41"):
    from normcap.screengrab import dbus_shell

    grab_screens = dbus_shell.grab_screens

else:
    from normcap.screengrab import dbus_portal

    grab_screens = dbus_portal.grab_screens
