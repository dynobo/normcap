import sys
from typing import Callable

from normcap.screengrab import utils
from normcap.screengrab.utils import (
    has_screenshot_permission,
    macos_open_privacy_settings,
    macos_request_screenshot_permission,
    macos_reset_screenshot_permission,
)


def _is_pyside6_64plus() -> bool:
    import PySide6

    version_tuple = PySide6.__version__.split(".")
    return version_tuple[0] >= "6" and version_tuple[1] >= "4"


def get_capture_func() -> Callable:

    # fmt: off
    if sys.platform != "linux" or not utils.has_wayland_display_manager():
        from normcap.screengrab import qt

        return qt.capture

    if utils.has_dbus_portal_support():
        if _is_pyside6_64plus():
            from normcap.screengrab import dbus_portal
            return dbus_portal.capture
        else:
            from normcap.screengrab import dbus_portal_legacy
            return dbus_portal_legacy.capture

    from normcap.screengrab import dbus_shell

    return dbus_shell.capture
    # fmt: on


__all__ = [
    "has_screenshot_permission",
    "macos_open_privacy_settings",
    "macos_request_screenshot_permission",
    "macos_reset_screenshot_permission",
    "get_capture_func",
]
