"""Capture screenshots for all screens using org.freedesktop.portal.Desktop."""

import logging
import random
from urllib.parse import urlparse

from PySide6 import QtCore, QtDBus, QtGui

from normcap.screengrab import ScreenshotRequestError, ScreenshotResponseError
from normcap.screengrab.utils import split_full_desktop_to_screens

# FIXME: Not working with Gnome 43 in FlatPak?

logger = logging.getLogger(__name__)


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
    on_response = QtCore.Signal(str)

    def grab_full_desktop(self) -> None:
        bus = QtDBus.QDBusConnection.sessionBus()

        base = bus.baseService()[1:].replace(".", "_")

        pseudo_unique_str = "".join(random.choice("abcdefghijklmnop") for _ in range(8))
        token = f"normcap_{pseudo_unique_str}"
        object_path = f"/org/freedesktop/portal/desktop/request/{base}/{token}"

        request = OrgFreedesktopPortalRequestInterface(object_path, bus, self)
        request.Response.connect(self.got_signal)

        interface = QtDBus.QDBusInterface(
            "org.freedesktop.portal.Desktop",
            "/org/freedesktop/portal/desktop",
            "org.freedesktop.portal.Screenshot",
            bus,
            self,
        )

        result = interface.call(
            "Screenshot", "", {"interactive": False, "handle_token": token}
        )
        if not (
            isinstance(result, QtDBus.QDBusMessage)
            and isinstance(result.arguments()[0], QtDBus.QDBusObjectPath)
        ):
            raise ScreenshotRequestError("No object path received from xdg-portal.")

        logger.debug(
            "Requested screenshot. Object path: %s", result.arguments()[0].path()
        )

    def got_signal(self, message: QtDBus.QDBusMessage) -> None:
        code, arg = message.arguments()
        if code == 1:
            raise ScreenshotResponseError("Error code received from xdg-portal.")

        logger.debug("Received response from freedesktop.portal.request: %s", message)

        uri = str(message).split('[Variant(QString): "')[1]
        uri = uri.split('"]}')[0]
        # TODO: Parse from arguments instead?
        # arg.beginArray()
        # while not arg.atEnd():
        #     arg.beginMap()
        #     while not arg.atEnd():
        #         arg.beginMapEntry()
        #         key = arg.asVariant()
        #         value = arg.asVariant()
        #         # v = value.variant()
        #         arg.endMapEntry()
        #     arg.endMap()
        # arg.endArray()
        self.on_response.emit(uri)


def capture() -> list[QtGui.QImage]:
    """Capture screenshots for all screens using org.freedesktop.portal.Desktop.

    This methods works gnome-shell >=v41 and wayland.
    """
    logger.debug("Use capture method: DBUS portal")

    loop = QtCore.QEventLoop()
    result = []

    def _signal_triggered(uri: str) -> None:
        result.append(uri)
        loop.exit()

    def _timeout_triggered() -> None:
        loop.exit()
        raise TimeoutError()

    portal = OrgFreedesktopPortalScreenshot()
    portal.on_response.connect(_signal_triggered)

    timeout_seconds = 10
    try:
        QtCore.QTimer.singleShot(0, portal.grab_full_desktop)
        QtCore.QTimer.singleShot(timeout_seconds * 1000, _timeout_triggered)
        loop.exec_()
    except TimeoutError as e:
        logger.error("Screenshot not received within %s seconds", timeout_seconds)
        raise e
    except ScreenshotRequestError as e:
        logger.error("Request to xdg-portal failed.")
        raise e
    except ScreenshotResponseError:
        logger.warning(
            "Couldn't get screenshort via xdg-portal. Did the screenshot dialog got "
            + "cancelled or are permissions missing?"
        )
    finally:
        portal.on_response.disconnect(_signal_triggered)

    if not result:
        logger.warning("No screenshot taken.")
        return []

    uri = result[0]
    full_image = QtGui.QImage(urlparse(uri).path)
    return split_full_desktop_to_screens(full_image)
