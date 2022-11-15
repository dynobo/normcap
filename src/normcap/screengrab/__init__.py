import sys
from typing import Callable

from normcap.screengrab import utils
from normcap.screengrab.utils import (
    has_screenshot_permission,
    macos_open_privacy_settings,
    macos_request_screenshot_permission,
    macos_reset_screenshot_permission,
)


def get_capture_func() -> Callable:
    # pylint: disable=import-outside-toplevel
    # fmt: off
    if sys.platform != "linux" or not utils.has_wayland_display_manager():
        from normcap.screengrab import qt
        return qt.capture

    if utils.has_dbus_portal_support():
        from normcap.screengrab import dbus_portal
        return dbus_portal.capture

    from normcap.screengrab import dbus_shell
    return dbus_shell.capture
    # fmt: on
    # pylint: enable=import-outside-toplevel


__all__ = [
    "has_screenshot_permission",
    "macos_open_privacy_settings",
    "macos_request_screenshot_permission",
    "macos_reset_screenshot_permission",
    "get_capture_func",
]
