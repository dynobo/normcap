import ctypes
import ctypes.util
import logging
import subprocess
import sys
from typing import Any, cast

from PySide6 import QtCore, QtGui, QtWidgets

from normcap.gui.constants import APP_ID, OPEN_ISSUE_TEXT
from normcap.gui.localization import _
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
    cmd = ["tccutil", "reset", "ScreenCapture", APP_ID]
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


# TODO: Pull the permission dialog out to gui
class DbusPortalPermissionDialog(QtWidgets.QDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        # L10N: Title of screenshot permission dialog only shown on Linux + Wayland.
        title = _("NormCap - Screenshot Permission")
        # L10N: Text of screenshot permission dialog only shown on Linux + Wayland.
        text = _(
            "<h3>Request screenshot permission?</h3>"
            "<p>NormCap needs permission to take screenshots, which is essential"
            "<br> for its functionality. It appears these permissions are "
            "currently missing.</p>"
            "<p>Click 'OK' to trigger a system prompt requesting access.<br>"
            "Please allow this, otherwise NormCap may not work properly.</p>"
        )

        self.setWindowTitle(title)
        self.setWindowIcon(QtGui.QIcon(":normcap"))
        self.setMinimumSize(600, 300)
        self.setModal(True)

        main_vbox = QtWidgets.QVBoxLayout()
        main_vbox.addWidget(self._create_message(text))
        main_vbox.addStretch()
        main_vbox.addLayout(self._create_footer())
        self.setLayout(main_vbox)

    @staticmethod
    def _create_message(text: str) -> QtWidgets.QLabel:
        message = QtWidgets.QLabel(text)
        message.setWordWrap(True)
        return message

    def _create_footer(self) -> QtWidgets.QLayout:
        footer_hbox = QtWidgets.QHBoxLayout()
        footer_hbox.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        footer_hbox.setContentsMargins(0, 0, 2, 0)

        open_issue_text = QtWidgets.QLabel(OPEN_ISSUE_TEXT)

        # L10N: Permission request dialog button
        ok_button = QtWidgets.QPushButton(_("Ok"))
        ok_button.clicked.connect(self.accept_button_pressed)
        ok_button.setDefault(True)

        # L10N: Permission request dialog button
        cancle_button = QtWidgets.QPushButton(_("Cancel"))
        cancle_button.clicked.connect(self.reject_button_pressed)

        footer_hbox.addWidget(open_issue_text)
        footer_hbox.addStretch()
        footer_hbox.addWidget(ok_button)
        footer_hbox.addWidget(cancle_button)
        return footer_hbox

    def accept_button_pressed(self) -> None:
        if not dbus_portal:
            raise ModuleNotFoundError(
                "Portal permission requested, but dbus_portal could not been imported!"
            )

        self.setEnabled(False)

        screenshots = []
        try:
            logger.debug("Request screenshot.")
            screenshots = dbus_portal.capture()
        except TimeoutError:
            logger.warning("Timeout when taking screenshot!")
        except PermissionError:
            logger.warning("Missing permission for taking screenshot!")

        self.setEnabled(True)
        self.setResult(len(screenshots) > 0)
        self.hide()

    def reject_button_pressed(self) -> None:
        logger.warning("Screenshot permission dialog was canceled!")
        self.setResult(False)
        self.hide()


def _dbus_portal_has_screenshot_permission() -> bool:
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
    permissions_granted = DbusPortalPermissionDialog().exec()
    if not permissions_granted:
        logger.warning("Requesting screenshot permissions on Wayland failed!")
        return False

    return True


def has_screenshot_permission() -> bool:
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
        return _dbus_portal_has_screenshot_permission()

    return True
