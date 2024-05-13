"""Capture screenshots for all screens using org.freedesktop.portal.Desktop."""

import logging
import random
import re
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

from PySide6 import QtCore, QtDBus, QtGui

from normcap.screengrab import system_info
from normcap.screengrab.post_processing import split_full_desktop_to_screens

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


class OrgFreedesktopPortalRequestInterface(QtDBus.QDBusAbstractInterface):
    Response = QtCore.Signal(QtDBus.QDBusMessage)

    def __init__(
        self, path: str, connection: QtDBus.QDBusConnection, parent: QtCore.QObject
    ) -> None:
        super().__init__(
            "org.freedesktop.portal.Desktop",
            path,
            "org.freedesktop.portal.Request",  # type: ignore
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
        object_path = f"/org/freedesktop/portal/desktop/request/{base}/{token}"

        request = OrgFreedesktopPortalRequestInterface(object_path, bus, self)
        request.Response.connect(self.on_response)

        interface = QtDBus.QDBusInterface(
            "org.freedesktop.portal.Desktop",
            "/org/freedesktop/portal/desktop",
            "org.freedesktop.portal.Screenshot",
            bus,
            self,
        )

        message = interface.call(
            "Screenshot", "", {"interactive": False, "handle_token": token}
        )
        logger.debug("DBus request message: %s", str(message))

        if (
            isinstance(message, QtDBus.QDBusMessage)
            and message.arguments()
            and isinstance(message.arguments()[0], QtDBus.QDBusObjectPath)
        ):
            logger.debug("Request accepted")
        else:
            msg = "No object path received from xdg-portal!"
            logger.error(msg)
            self.on_exception.emit(RuntimeError(msg))

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

    def got_signal(self, message: QtDBus.QDBusMessage) -> None:
        self.timeout_timer.stop()
        logger.debug("DBus signal message: %s", str(message))

        code, _ = message.arguments()
        all_okay_code = 0
        permission_denied_code = 2

        if code == permission_denied_code:
            msg = f"Permission denied for Screenshot via xdg-portal! Message: {message}"
            logger.error(msg)
            self.on_exception.emit(PermissionError(msg))
            return

        if code != all_okay_code:
            msg = f"Error code {code} received from xdg-portal!"
            logger.error(msg)
            self.on_exception.emit(RuntimeError(msg))
            return

        logger.debug("Parse response")
        # ONHOLD: Extracting DBusArgument as below should work, but it doesn't.
        #         As there doesn't seem to be another way to access the arguments,
        #         we workaround by parsing the URI from string representation.
        # _, arg = message.arguments()
        # QtDBus.QDBusMessage()
        # arg.beginArray()
        # while not arg.atEnd():
        #     arg.beginMap()
        #     while not arg.atEnd():
        #         arg.beginMapEntry()
        #         key = arg.asVariant()
        #         value = arg.asVariant()
        #         arg.endMapEntry()
        #     arg.endMap()
        # arg.endArray()

        reg_uri = r"""
                  \[Variant\(QString\)\:\ \"  # start of URI object
                  (.*)                       # URI itself
                  \"\]\}                     # end of URI object
                  """
        result = re.search(reg_uri, str(message), re.VERBOSE)

        if not result:
            msg = f"Couldn't parse URI from message: {message}"
            logger.error(msg)
            self.on_exception.emit(RuntimeError(message))
            return

        uri = result.group(1)
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
    # TODO: Specify closer!
    return sys.platform == "linux"


def is_installed() -> bool:
    # TODO: What's with KDE?
    gnome_version = system_info.get_gnome_version()
    return not gnome_version or gnome_version >= "41"


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
