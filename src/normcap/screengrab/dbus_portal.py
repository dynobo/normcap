"""Capture screenshots for all screens using org.freedesktop.portal.Desktop."""

import logging
import random
from urllib.parse import urlparse

from PySide6 import QtCore, QtDBus, QtGui

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
        if args := result.arguments():
            if isinstance(args[0], QtDBus.QDBusObjectPath):
                logger.debug("Requested screenshot. Object path: %s", args[0].path())

    def got_signal(self, message: QtDBus.QDBusMessage) -> None:
        code, arg = message.arguments()
        if code == 1:
            logger.warning(
                "Couldn't get screenshort via freedesktop.portal. Did the "
                + "dialog got cancelled or are permissions missing?"
            )
            self.on_response.emit("")

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
    portal = OrgFreedesktopPortalScreenshot()

    loop = QtCore.QEventLoop()
    result = []

    def signal_triggered(uri: str) -> None:
        result.append(uri)
        loop.exit()

    portal.on_response.connect(signal_triggered)
    QtCore.QTimer.singleShot(0, portal.grab_full_desktop)

    # Timeout after 15sec
    timer = QtCore.QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    timer.start(15_000)

    loop.exec_()

    timer.stop()
    portal.on_response.disconnect(signal_triggered)
    timer.timeout.disconnect(loop.quit)

    full_image = None
    if uri := result[0]:
        full_image = QtGui.QImage(urlparse(uri).path)

    return split_full_desktop_to_screens(full_image) if full_image else []
