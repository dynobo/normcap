import ctypes
import ctypes.util
import logging
import subprocess
import sys
from typing import Any, Optional, cast

from PySide6 import QtGui, QtWidgets

from normcap.screengrab import system_info

try:
    from normcap.screengrab.handlers import dbus_portal

except ImportError:
    dbus_portal = cast(Any, None)


logger = logging.getLogger(__name__)

DEFAULT_MACOS_DIALOG_TEXT = (
    "This application is missing the permission for 'Screen Recording'."
    "\n\n"
    "Grant it via the dialog that will appear after you clicked 'Ok' "
    "or via 'System Settings' > 'Privacy & Security'."
    "\n\n"
    "Then restart this application."
)
DEFAULT_LINUX_DIALOG_TEXT = (
    "<b>This application does not have permission to take screenshots!</b><br>"
    "<br>"
    "Click 'OK' to trigger a request for permission: A system<br>"
    "dialog should appear and ask you to confirm granting that<br>"
    "permission.<br>"
    "<br>"
    "(Sometimes, this might not work. If that is the case for you<br>"
    "then please report this as bug to the application author.)"
)


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
    return has_permission


def _macos_request_screenshot_permission() -> None:
    """Use CoreGraphics to request screen recording permissions."""
    try:
        cg = _macos_load_core_graphics()
        logger.debug("Request screen recording access")
        cg.CGRequestScreenCaptureAccess()
    except Exception as e:
        logger.warning("Couldn't request screen recording permission: %s", e)


def _macos_open_privacy_settings() -> None:
    link_to_preferences = (
        "x-apple.systempreferences:com.apple.preference.security"
        "?Privacy_ScreenCapture"
    )
    try:
        if sys.platform != "darwin":
            logger.error("Couldn't open macOS privacy settings on non macOS platform.")
            return

        subprocess.run(
            ["open", link_to_preferences],  # noqa: S607
            shell=False,  # noqa: S603
            check=True,
            timeout=30,
        )
    except Exception:
        logger.exception("Couldn't open macOS privacy settings.")


def macos_reset_screenshot_permission() -> None:
    """Use tccutil to reset permissions for current application."""
    logger.info("Reset screen recording permissions for eu.dynobo.normcap")
    cmd = ["tccutil", "reset", "ScreenCapture", "eu.dynobo.normcap"]
    try:
        completed_proc = subprocess.run(
            cmd,
            shell=False,  # noqa: S603
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


def macos_show_request_permission_dialog(title: str, text: str) -> bool:
    QtWidgets.QMessageBox.critical(
        None,
        title,
        text,
        buttons=QtWidgets.QMessageBox.StandardButton.Ok,
    )
    # Trigger permission request to make the NormCap entry available in settings
    _macos_request_screenshot_permission()

    # On macOS, an application is required to restart after receiving the permission,
    # therefore it will never be there when the permission just got requested
    return False


class DbusPortalPermissionDialog(QtWidgets.QDialog):
    def __init__(
        self,
        title: str,
        text: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.capture: list[QtGui.QImage] = []

        self.setWindowTitle(title)

        self.button_box = self._create_button_box()
        self.button_box.accepted.connect(self.accept_button_pressed)
        self.button_box.rejected.connect(self.reject_button_pressed)

        label = QtWidgets.QLabel(text)
        label.setOpenExternalLinks(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    @staticmethod
    def _create_button_box() -> QtWidgets.QDialogButtonBox:
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        cancel_button = button_box.button(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        cancel_button.setAutoDefault(False)
        cancel_button.setDefault(False)

        ok_button = button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        ok_button.setDefault(True)
        return button_box

    def accept_button_pressed(self) -> None:
        if not dbus_portal:
            raise ModuleNotFoundError(
                "Portal permission requested, but dbus_portal could not been imported!"
            )

        self.setEnabled(False)
        try:
            logger.debug("Request screenshot with interactive=True")
            self.capture = dbus_portal._synchronized_capture(interactive=True)
        except TimeoutError:
            logger.warning("Timeout when taking screenshot!")
        self.setResult(0)
        self.setEnabled(True)
        self.hide()

    def reject_button_pressed(self) -> None:
        self.setResult(1)
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
    return len(result) > 0


def dbus_portal_show_request_permission_dialog(title: str, text: str) -> bool:
    window = DbusPortalPermissionDialog(title=title, text=text + "<br>")
    choice = window.exec()

    if choice != 0:
        logger.warning("Screenshot permission dialog was canceled!")
        return False

    if not window.capture:
        logger.warning("Permission for screenshot is still missing!")
        return False

    return True


def has_screenshot_permission() -> bool:
    logger.debug("Checking screenshot permission")
    if sys.platform == "darwin":
        return _macos_has_screenshot_permission()
    if sys.platform == "linux" and not system_info.has_wayland_display_manager():
        return True
    if sys.platform == "linux" and system_info.has_wayland_display_manager():
        return _dbus_portal_has_screenshot_permission()
    if sys.platform == "win32":
        return True
    raise NotImplementedError("Missing permission check for this platform.")


def request_screenshot_permission(
    dialog_title: str = "Error",
    macos_dialog_text: str = DEFAULT_MACOS_DIALOG_TEXT,
    linux_dialog_text: str = DEFAULT_LINUX_DIALOG_TEXT,
) -> None:
    if sys.platform == "win32":
        logger.debug(
            "Not necessary to request screenshot permission on Windows. Skipping."
        )
        return

    if sys.platform == "linux" and not system_info.has_wayland_display_manager():
        logger.debug(
            "Not necessary to request screenshot permission on Linux, if the "
            "display manager is not Wayland. Skipping."
        )
        return

    if sys.platform == "linux" and system_info.has_wayland_display_manager():
        logger.debug("Show request permission dialog.")
        dbus_portal_show_request_permission_dialog(
            title=dialog_title, text=linux_dialog_text
        )
        return

    if sys.platform == "darwin":
        logger.debug("Show request permission dialog.")
        macos_show_request_permission_dialog(title=dialog_title, text=macos_dialog_text)

    raise NotImplementedError(
        "Missing permission request implementation this platform."
    )
