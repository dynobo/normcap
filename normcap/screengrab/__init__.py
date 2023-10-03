import logging
import sys
from typing import Protocol

from PySide6 import QtGui

from normcap.screengrab import utils
from normcap.screengrab.utils import (
    has_screenshot_permission,
    macos_open_privacy_settings,
    macos_request_screenshot_permission,
    macos_reset_screenshot_permission,
)


class ScreenshotError(Exception):
    ...


class ScreenshotResponseError(ScreenshotError):
    ...


class ScreenshotRequestError(ScreenshotError):
    ...


logger = logging.getLogger(__name__)


class CaptureFunc(Protocol):
    def __call__(self) -> list[QtGui.QImage]:
        ...  # pragma: no cover


def get_capture_func() -> CaptureFunc:
    # fmt: off
    if sys.platform != "linux" or not utils.has_wayland_display_manager():
        logger.debug("Select capture method QT")
        from normcap.screengrab import qt
        return qt.capture

    if utils.has_grim_support():
        logger.debug("Select capture method grim")
        from normcap.screengrab import grim
        return grim.capture

    if utils.has_dbus_portal_support():
        logger.debug("Select capture method DBUS portal")
        from normcap.screengrab import dbus_portal
        return dbus_portal.capture


    logger.debug("Select capture method DBUS shell")
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
