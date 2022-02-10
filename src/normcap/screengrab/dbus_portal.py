"""Some utility functions."""

import logging
import secrets
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from jeepney.bus_messages import MatchRule, message_bus  # type: ignore
from jeepney.io.blocking import Proxy, open_dbus_connection  # type: ignore
from jeepney.wrappers import (  # type: ignore
    DBusErrorResponse,
    MessageGenerator,
    new_method_call,
)
from PySide6 import QtGui

# TODO: Get rid of jeepney


logger = logging.getLogger(__name__)
from normcap.screengrab.utils import split_full_desktop_to_screens


class FreedesktopPortalScreenshot(MessageGenerator):
    """Using Portal API to get screenshot.

    This has to be used for gnome-shell 41.+ on Wayland.
    """

    interface = "org.freedesktop.portal.Screenshot"

    def __init__(self):
        """Init jeepney message generator."""
        super().__init__(
            object_path="/org/freedesktop/portal/desktop",
            bus_name="org.freedesktop.portal.Desktop",
        )

    def grab(self, parent_window, options):
        """Ask for screenshot."""
        return new_method_call(self, "Screenshot", "sa{sv}", (parent_window, options))


def grab_full_desktop() -> QtGui.QImage:
    """Capture rect of screen on gnome systems using wayland."""
    logger.debug("Use capture method: DBUS portal")

    image = QtGui.QImage()

    _, temp_name = tempfile.mkstemp(prefix="normcap")
    try:
        connection = open_dbus_connection(bus="SESSION")

        token = f"normcap_{secrets.token_hex(8)}"
        sender_name = connection.unique_name[1:].replace(".", "_")
        handle = f"/org/freedesktop/portal/desktop/request/{sender_name}/{token}"

        response_rule = MatchRule(
            type="signal", interface="org.freedesktop.portal.Request", path=handle
        )
        Proxy(message_bus, connection).AddMatch(response_rule)

        with connection.filter(response_rule) as responses:
            msg = FreedesktopPortalScreenshot().grab(
                "", {"handle_token": ("s", token), "interactive": ("b", False)}
            )
            connection.send_and_get_reply(msg)
            response = connection.recv_until_filtered(responses)

        response_code, response_body = response.body
        assert response_code == 0 and "uri" in response_body

        image = QtGui.QImage(urlparse(response_body["uri"][1]).path)

    except AssertionError as e:
        logger.warning("Couldn't take screenshot with DBUS. Got cancelled?")
        raise e from e
    except DBusErrorResponse as e:
        if "invalid params" in [d.lower() for d in e.data]:
            logger.info("ScreenShot with DBUS failed with 'invalid params'")
        else:
            logger.exception("ScreenShot with DBUS through exception")
    finally:
        Path(temp_name).unlink()

    return image


# FIRST TESTS WITH QTDBUS

# def grab_full_desktop() -> QtGui.QImage:
#     """Capture rect of screen on gnome systems using wayland.
#     QDBusInterface interface(QStringLiteral("org.freedesktop.portal.Desktop"),
#     QStringLiteral("/org/freedesktop/portal/Screenshot"),
#     QStringLiteral("org.freedesktop.portal.Screenshot"));
#         QDBusPendingReply<QDBusObjectPath> reply;

#         reply = interface.call(QStringLiteral("Screenshot"), "", QVariantMap());

#         if (reply.isError()) {
#                 qCritical("Invalid reply from DBus: %s", qPrintable(reply.error().message()));
#         } else {
#             qCritical("Dbus success: %s", qPrintable(reply.argumentAt<0>().path()));
#         }
#     """
#     item = "org.freedesktop.portal.Desktop"
#     path = "/org/freedesktop/portal/desktop"
#     interface = "org.freedesktop.portal.Screenshot"
#     method = "Screenshot"
#     token = f"normcap_{secrets.token_hex(8)}"

#     bus = QtDBus.QDBusConnection.sessionBus()
#     if not bus.isConnected():
#         logger.error("Not connected to dbus!")

#     interface = QtDBus.QDBusInterface(item, path, interface, bus)
#     reply = interface.call(method, "", {"handle_token": token, "interactive": False})

#     class DbusTest(QtCore.QObject):
#         def __init__(self, path, bus):
#             super(DbusTest, self).__init__()
#             # bus = QtDBus.QDBusConnection.sessionBus()
#             print("Connected")

#         @QtCore.Slot(str)
#         @QtCore.Slot(QtDBus.QDBusMessage)
#         def testMessage(self, msg):
#             print("re")
#             print(msg)
#             exit(0)

#     app = QtWidgets.QApplication.instance()
#     path = "/" + "/".join(str(reply).split("/")[1:]).split("]")[0]
#     discoverer = DbusTest("/" + path, bus)

#     # bus.registerObject("/", discoverer)
#     interface2 = QtDBus.QDBusInterface("org.freedesktop.portal.Desktop", path, "", bus)
#     s = interface2.connect(
#         "Response",
#         discoverer,
#         "testMessage",
#     )
#     result = app.exec_()

#     logger.debug("Use capture method: DBUS portal")


def grab_screens() -> list[QtGui.QImage]:
    """Capture screenshots for all screens using org.freedesktop.portal.Desktop.

    This methods works gnome-shell >=v41 and wayland.
    """
    full_image = grab_full_desktop()
    return split_full_desktop_to_screens(full_image)
