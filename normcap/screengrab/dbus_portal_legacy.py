"""Capture screenshots for all screens using org.freedesktop.portal.Desktop.

Legacy version using jeepney.

# FIXME: Not working with Gnome 43 in FlatPak (If new version doesnt work their, either)
# TODO: Remove legacy dbus portal module once it is deprecated. Check in 2023-05-01.

AppImage related dependency chain necessary to be resolved before removal:

- PySide6 v6.1+
  Currently, only v6.2 can be installed, in which the new implementatio (dbus_portal.py)
  doesn't receive any response for unknown reasons.

- glibc 2.28+
  PySide6 packaging got changed between 6.2 and 6.4 to actually check for glibc2.28+.
  As this is not present on Ubuntu 16.04 AppImage, PySide6 v6.4+ won't install.
  Sidenote: the missing glibc 2.28+ probably also is the reason for some failures on old
  host distributions and during the appimage.github.io checks.
  TODO: Let's retry appimage.github.io submission
  Details see https://lists.qt-project.org/pipermail/pyside/2022-December/003253.html

- Briefcase support image on Ubuntu 18.04.6 LTS
  This versions ships with the Glib required. The current minimal required version for
  AppImages (16.04) should be retired around April 2023 https://wiki.ubuntu.com/Releases
"""

import logging
import random
from typing import Optional
from urllib.parse import urlparse

from jeepney.bus_messages import MatchRule, Message, message_bus
from jeepney.io.blocking import Proxy, open_dbus_connection
from jeepney.wrappers import DBusErrorResponse, MessageGenerator, new_method_call
from PySide6 import QtGui

from normcap.screengrab.utils import split_full_desktop_to_screens

logger = logging.getLogger(__name__)


class FreedesktopPortalScreenshot(MessageGenerator):
    """Use Portal API to get screenshot.

    This has to be used for gnome-shell 41.+ on Wayland.
    """

    interface = "org.freedesktop.portal.Screenshot"

    def __init__(self) -> None:
        """Init jeepney message generator."""
        super().__init__(
            object_path="/org/freedesktop/portal/desktop",
            bus_name="org.freedesktop.portal.Desktop",
        )

    def grab(self, parent_window: str, options: dict) -> Message:
        """Ask for screenshot."""
        # method_name = "org.freedesktop.portal.Screenshot"
        return new_method_call(self, "Screenshot", "sa{sv}", (parent_window, options))


def grab_full_desktop() -> Optional[QtGui.QImage]:
    """Capture rect of screen on gnome systems using wayland."""
    image = None
    try:
        connection = open_dbus_connection(bus="SESSION")
        pseudo_unique_str = "".join(random.choice("abcdefghijklmnop") for _ in range(8))
        token = f"normcap_{pseudo_unique_str}"
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
        if response_code != 0 or "uri" not in response_body:
            raise AssertionError()

        image = QtGui.QImage(urlparse(response_body["uri"][1]).path)

    except AssertionError:
        logger.warning("Couldn't take screenshot with DBUS. Got cancelled?")
    except DBusErrorResponse as e:
        if "invalid params" in [d.lower() for d in e.data]:
            logger.info("ScreenShot with DBUS failed with 'invalid params'")
        else:
            logger.exception("ScreenShot with DBUS through exception")

    return image


def capture() -> list[QtGui.QImage]:
    """Capture screenshots for all screens using org.freedesktop.portal.Desktop.

    This methods works gnome-shell >=v41 and wayland.
    """
    full_image = grab_full_desktop()
    return split_full_desktop_to_screens(full_image) if full_image else []
