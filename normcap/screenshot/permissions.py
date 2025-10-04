import ctypes
import ctypes.util
import logging
import subprocess
import sys
from typing import Any, cast

from PySide6 import QtWidgets

from normcap import app_id
from normcap.screenshot import models
from normcap.screenshot.main import get_available_handlers

try:
    from normcap.screenshot.handlers import dbus_portal

except ImportError:
    dbus_portal = cast(Any, None)


logger = logging.getLogger(__name__)


def _macos_load_core_graphics() -> ctypes.CDLL:
    if core_graphics := ctypes.util.find_library("CoreGraphics"):
        return ctypes.cdll.LoadLibrary(core_graphics)
    raise RuntimeError("Couldn't load CoreGraphics")


def _macos_has_screenshot_permission() -> bool:
    """Use CoreGraphics to check if application has screen recording permissions.

    Returns:
        True if permissions are available or can't be detected.
    """
    try:
        cg = _macos_load_core_graphics()
        has_permission = bool(cg.CGPreflightScreenCaptureAccess())
    except Exception as e:
        has_permission = True
        logger.warning("Couldn't detect screen recording permission: %s", e)
        logger.warning("Assuming screen recording permission is %s", has_permission)

    if not has_permission:
        # Reset privacy permission in case of new NormCap version. This is necessary
        # because somehow the setting is associated with the binary and won't work
        # after it got updated.
        macos_reset_screenshot_permission()

    return has_permission


def macos_request_screenshot_permission() -> None:
    """Use CoreGraphics to request screen recording permissions."""
    try:
        cg = _macos_load_core_graphics()
        logger.debug("Request screen recording access")
        cg.CGRequestScreenCaptureAccess()
    except Exception as e:
        logger.warning("Couldn't request screen recording permission: %s", e)


def _macos_open_privacy_settings() -> None:
    link_to_preferences = (
        "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"
    )
    try:
        if sys.platform != "darwin":
            logger.error("Couldn't open macOS privacy settings on non macOS platform.")
            return

        subprocess.run(  # noqa: S603
            ["open", link_to_preferences],  # noqa: S607
            shell=False,
            check=True,
            timeout=30,
        )
    except Exception:
        logger.exception("Couldn't open macOS privacy settings.")


def macos_reset_screenshot_permission() -> None:
    """Use tccutil to reset permissions for current application."""
    logger.info("Reset screen recording permissions for com.github.dynobo.normcap")
    cmd = ["tccutil", "reset", "ScreenCapture", app_id]
    try:
        completed_proc = subprocess.run(  # noqa: S603
            cmd,
            shell=False,
            encoding="utf-8",
            check=False,
            timeout=10,
        )
        if completed_proc.returncode != 0:
            logger.error(
                "Failed resetting screen recording permissions: %s %s",
                completed_proc.stdout,
                completed_proc.stderr,
            )
    except Exception:
        logger.exception("Couldn't reset screen recording permissions.")
    finally:
        macos_request_screenshot_permission()


def _dbus_portal_has_screenshot_permission(
    request_portal_dialog: type[QtWidgets.QDialog],
) -> bool:
    if not dbus_portal:
        raise ModuleNotFoundError(
            "Portal permission requested, but dbus_portal could not been imported!"
        )
    result = []
    try:
        result = dbus_portal.capture()
    except (PermissionError, TimeoutError) as exc:
        logger.warning("Screenshot permissions on Wayland seem missing.", exc_info=exc)

    if len(result) > 0:
        return True

    logger.info("Trying to request permissions via dialog.")
    permissions_granted = request_portal_dialog(dbus_portal.capture()).exec()
    if not permissions_granted:
        logger.warning("Requesting screenshot permissions on Wayland failed!")
        return False

    return True


def has_screenshot_permission(request_portal_dialog: type[QtWidgets.QDialog]) -> bool:
    """Check and ask for screenshot permissions.

    Args:
        request_portal_dialog: Qt Dialog which takes as init arg a callable which
            queries dbus portal for screenshot. The dialog should return True, if
            screenshots could be retrieved or False if not.

    Returns:
        If a handler with screenshot permissions was found.
    """
    logger.debug("Checking screenshot permission")

    if sys.platform == "win32":
        return True

    if sys.platform == "darwin":
        return _macos_has_screenshot_permission()

    handlers = get_available_handlers()
    primary_handler = handlers[0] if handlers else None
    if not primary_handler:
        raise RuntimeError(
            "Could not identify a screenshot method for this system configuration."
        )

    if primary_handler == models.Handler.DBUS_PORTAL:
        return _dbus_portal_has_screenshot_permission(request_portal_dialog)

    return True
