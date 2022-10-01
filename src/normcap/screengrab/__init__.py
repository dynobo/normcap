import sys

from normcap.screengrab import utils
from normcap.screengrab.utils import (
    has_screenshot_permission,
    macos_open_privacy_settings,
    macos_request_screenshot_permission,
    macos_reset_screenshot_permission,
)


def _get_appropriate_capture():
    platform_module = None

    # pylint: disable=import-outside-toplevel
    if sys.platform != "linux" or not utils.has_wayland_display_manager():
        import normcap.screengrab.qt as platform_module
    elif utils.has_dbus_portal_support():
        import normcap.screengrab.dbus_portal as platform_module
    else:
        import normcap.screengrab.dbus_shell as platform_module
    # pylint: enable=import-outside-toplevel

    if not platform_module:
        raise RuntimeError("Couldn't load appropiate screen capture method.")

    return platform_module.capture


capture = _get_appropriate_capture()
