import logging
import sys
from typing import Protocol

from PySide6 import QtGui

from normcap.screengrab import utils

logger = logging.getLogger(__name__)


class CaptureFunc(Protocol):
    def __call__(self) -> list[QtGui.QImage]:
        ...  # pragma: no cover


def get_capture_func() -> CaptureFunc:
    # fmt: off
    if sys.platform != "linux" or not utils.is_wayland_display_manager():
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
