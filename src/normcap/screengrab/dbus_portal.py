"""Capture screenshots for all screens using org.freedesktop.portal.Desktop."""

import logging
import secrets
from typing import Optional
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
        # method_name = "org.freedesktop.portal.Screenshot"
        return new_method_call(self, "Screenshot", "sa{sv}", (parent_window, options))


def grab_full_desktop() -> Optional[QtGui.QImage]:
    """Capture rect of screen on gnome systems using wayland."""
    logger.debug("Use capture method: DBUS portal")

    image = None

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
            response = connection.recv_until_filtered(responses, timeout=15)

        response_code, response_body = response.body
        assert response_code == 0 and "uri" in response_body

        image = QtGui.QImage(urlparse(response_body["uri"][1]).path)

    except AssertionError as e:
        logger.warning("Couldn't take screenshot with DBUS. Got cancelled?")
    except DBusErrorResponse as e:
        if "invalid params" in [d.lower() for d in e.data]:
            logger.info("ScreenShot with DBUS failed with 'invalid params'")
        else:
            logger.exception("ScreenShot with DBUS through exception")

    return image


def grab_screens() -> list[QtGui.QImage]:
    """Capture screenshots for all screens using org.freedesktop.portal.Desktop.

    This methods works gnome-shell >=v41 and wayland.
    """
    full_image = grab_full_desktop()
    if not full_image:
        return []

    return split_full_desktop_to_screens(full_image)
