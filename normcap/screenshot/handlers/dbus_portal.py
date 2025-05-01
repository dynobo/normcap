"""Capture screenshots for all screens using org.freedesktop.portal.Desktop."""

import logging
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

from PySide6 import QtCore, QtDBus, QtGui

from normcap.screenshot.post_processing import split_full_desktop_to_screens

logger = logging.getLogger(__name__)

install_instructions = ""

# Note on Request Timeout:
#
# Unfortunately, the dbus portal does not return any error message, in case the
# screenshot could not be taken (e.g. missing permission). It just doesn't return any
# response. Therefore, we need to rely on a timeout between the screenshot request and
# its (potential) response to not keep waiting indefinitely.
#
# The value set below is somewhat arbitrary and a trade-off between enabling edge cases
# with high delays (e.g. in high resolution multi monitor setups) and a short delay
# between action and error message, which is desired from a UX perspective.
#
# We started with a 7 seconds timeout, but this turned out to be too low for at least
# one user, therefore it got increased.
#
# ONHOLD: Check in 2024 if the portal was updated to always return a response message.
TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class DBUS:
    DESKTOP_SERVICE: str = "org.freedesktop.portal.Desktop"
    DESKTOP_PATH: str = "/org/freedesktop/portal/desktop"
    SCREENSHOT_INTERFACE: str = "org.freedesktop.portal.Screenshot"
    REQUEST_INTERFACE: str = "org.freedesktop.portal.Request"
    REQUEST_PATH: str = "/org/freedesktop/portal/desktop/request"
    INTROSPECTABLE_SERVICE: str = "org.freedesktop.DBus.Introspectable"


class OrgFreedesktopPortalRequestInterface(QtDBus.QDBusAbstractInterface):
    Response = QtCore.Signal(QtDBus.QDBusMessage)

    def __init__(
        self, path: str, connection: QtDBus.QDBusConnection, parent: QtCore.QObject
    ) -> None:
        super().__init__(
            DBUS.DESKTOP_SERVICE,
            path,
            DBUS.REQUEST_INTERFACE,  # type: ignore
            connection,
            parent,
        )


class OrgFreedesktopPortalScreenshot(QtCore.QObject):
    on_response = QtCore.Signal(QtDBus.QDBusMessage)
    on_result = QtCore.Signal(str)
    on_exception = QtCore.Signal(Exception)

    def __init__(
        self,
        parent: Optional[QtCore.QObject] = None,
        interactive: bool = False,
        timeout_sec: int = 15,
    ) -> None:
        super().__init__(parent)
        self.interactive = interactive
        self.timeout_timer = self._get_timeout_timer(timeout_sec)
        self.on_response.connect(self.got_signal)

    def grab_full_desktop(self) -> None:
        bus = QtDBus.QDBusConnection.sessionBus()

        base = bus.baseService()[1:].replace(".", "_")

        random_str = "".join(random.choice("abcdefghi") for _ in range(8))  # noqa: S311
        token = f"normcap_{random_str}"
        object_path = f"{DBUS.REQUEST_PATH}/{base}/{token}"

        request = OrgFreedesktopPortalRequestInterface(object_path, bus, self)
        request.Response.connect(self.on_response)

        interface = QtDBus.QDBusInterface(
            DBUS.DESKTOP_SERVICE,
            DBUS.DESKTOP_PATH,
            DBUS.SCREENSHOT_INTERFACE,
            bus,
            self,
        )

        message = interface.call(
            "Screenshot", "", {"interactive": False, "handle_token": token}
        )
        logger.debug("DBus request message: %s", str(message))

        reply = QtDBus.QDBusReply(message)
        if not reply.isValid():
            error = reply.error().message()
            msg = f"DBus Screenshot responded with error: {error}; Reply: {reply}"
            logger.error(msg)
            self.on_exception.emit(RuntimeError(msg))
            return

        value = reply.value()

        if not isinstance(value, QtDBus.QDBusObjectPath):
            msg = (
                "No object path received from xdg-portal! "
                f"Value: {value}; Reply: {reply}"
            )
            logger.error(msg)
            self.on_exception.emit(RuntimeError(msg))
            return

        logger.debug("Request accepted")

    def _get_timeout_timer(self, timeout_sec: int) -> QtCore.QTimer:
        def _timeout_triggered() -> None:
            msg = f"No response from xdg-portal within {timeout_sec}s!"
            logger.error(msg)
            self.on_exception.emit(TimeoutError(msg))

        timeout_timer = QtCore.QTimer()
        timeout_timer.setSingleShot(True)
        timeout_timer.setInterval(timeout_sec * 1000)
        timeout_timer.timeout.connect(_timeout_triggered)
        return timeout_timer

    @staticmethod
    def extract_key_from_dbus_argument(
        arg: QtDBus.QDBusArgument, name: str
    ) -> Optional[str]:
        """Extract a value for a specific key from a nested QDBusArgument."""
        arg.beginArray()
        while not arg.atEnd():
            arg.beginMap()
            while not arg.atEnd():
                key = arg.asVariant()
                value = arg.asVariant()
                if key == name:
                    return value.variant()
            arg.endMap()
        arg.endArray()
        return None

    def got_signal(self, message: QtDBus.QDBusMessage) -> None:
        self.timeout_timer.stop()
        logger.debug("DBus signal message: %s", str(message))

        reply = QtDBus.QDBusReply(message)
        if not reply.isValid():
            msg = f"DBus signal message is invalid! Message: {message}"
            logger.error(msg)
            self.on_exception.emit(PermissionError(msg))
            return

        status_code = reply.value()
        all_okay_code = 0
        permission_denied_code = 2

        if status_code == permission_denied_code:
            msg = f"Permission denied for Screenshot via xdg-portal! Message: {message}"
            logger.error(msg)
            self.on_exception.emit(PermissionError(msg))
            return

        if status_code != all_okay_code:
            msg = f"Error code {status_code} received from xdg-portal!"
            logger.error(msg)
            self.on_exception.emit(RuntimeError(msg))
            return

        logger.debug("Process dbus response")
        _, arg = message.arguments()
        uri = self.extract_key_from_dbus_argument(arg=arg, name="uri")

        if not uri:
            msg = f"Could not retrieve URI from message: {message}"
            logger.error(msg)
            self.on_exception.emit(RuntimeError(message))
            return

        self.on_result.emit(uri)


def _synchronized_capture(interactive: bool) -> QtGui.QImage:
    loop = QtCore.QEventLoop()
    result = []
    exceptions = []

    def _signal_triggered(uri: str) -> None:
        result.append(uri)
        loop.exit()

    def _exception_triggered(uri: Exception) -> None:
        exceptions.append(uri)
        loop.exit()

    portal = OrgFreedesktopPortalScreenshot(
        interactive=interactive, timeout_sec=TIMEOUT_SECONDS
    )
    portal.on_result.connect(_signal_triggered)
    portal.on_exception.connect(_exception_triggered)

    portal.timeout_timer.start()
    QtCore.QTimer.singleShot(0, portal.grab_full_desktop)
    loop.exec()

    portal.on_result.disconnect(_signal_triggered)
    portal.on_exception.disconnect(_exception_triggered)

    for error in exceptions:
        raise error

    uri = result[0]
    parsed_uri = urlparse(uri)
    parsed_path = unquote(parsed_uri.path)

    image_path = Path(parsed_path)
    image = QtGui.QImage(image_path)

    # XDG Portal save the image file to the users xdg-pictures directory. To not let
    # them pile up, we try to remove it:
    try:
        image_path.unlink()
    except PermissionError:
        logger.warning("Missing permission to remove screenshot file '%s'!", image_path)

    return image


def is_compatible() -> bool:
    return sys.platform == "linux" or "bsd" in sys.platform


def is_installed() -> bool:
    session_bus = QtDBus.QDBusConnection.sessionBus()
    if not session_bus.isConnected():
        logger.warning("Cannot connect to the DBus session bus.")
        return False

    iface = QtDBus.QDBusInterface(
        DBUS.DESKTOP_SERVICE,
        DBUS.DESKTOP_PATH,
        DBUS.INTROSPECTABLE_SERVICE,
        session_bus,
    )
    if not iface.isValid():
        logger.warning(
            "DBus Screenshot is invalid: %s", session_bus.lastError().message()
        )
        return False

    message = iface.call("Introspect")
    reply = QtDBus.QDBusReply(message)
    if not reply.isValid():
        error = reply.error().message()
        logger.warning("Cannot introspect DBus: %s", error)
        return False

    value = reply.value()
    return DBUS.SCREENSHOT_INTERFACE in value


def capture() -> list[QtGui.QImage]:
    """Capture screenshots for all screens using org.freedesktop.portal.Desktop.

    This methods works gnome-shell >=v41 and wayland.

    In newer xdg-portal implementations, the first request has to be done in
    "interactive" mode, before the application is allowed to query screenshots without
    the dialog window in between.

    As there is no way to query for that permission, we try both:
    1. Try none-interactive mode
    2. If timeout triggers, retry in interactive mode with a helper window
    """
    try:
        image = _synchronized_capture(interactive=False)
    except TimeoutError as exc:
        raise TimeoutError("Timeout when taking screenshot!") from exc
    else:
        return split_full_desktop_to_screens(image)
