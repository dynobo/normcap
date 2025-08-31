"""Interact with the clipboard via DBus using jeepney.

This module provides a Pythonic interface to the org.freedesktop.portal.Clipboard
DBus interface.
"""

import logging
from collections.abc import Iterator
from typing import Any

from jeepney import DBusAddress, MatchRule, new_method_call
from jeepney.io.blocking import DBusConnection, open_dbus_connection

logger = logging.getLogger(__name__)

# DBus interface and bus name
CLIPBOARD_IFACE = "org.freedesktop.portal.Clipboard"
CLIPBOARD_PATH = "/org/freedesktop/portal/desktop"
CLIPBOARD_BUS = "org.freedesktop.portal.Desktop"


class Clipboard:
    """Synchronous wrapper for the org.freedesktop.portal.Clipboard DBus interface."""

    def __init__(self, connection: DBusConnection, address: DBusAddress) -> None:
        self.conn = connection
        self.address = address

    @classmethod
    def new(cls) -> "Clipboard":
        addr = DBusAddress(
            object_path=CLIPBOARD_PATH,
            bus_name=CLIPBOARD_BUS,
            interface=CLIPBOARD_IFACE,
        )
        conn = open_dbus_connection()
        return cls(conn, addr)

    def request(self, session_path: str) -> None:
        # session_path: DBus object path of the session
        msg = new_method_call(
            self.address, "RequestClipboard", "oa{sv}", (session_path, {})
        )
        logger.info("Request: %s", msg)
        reply = self.conn.send_and_get_reply(msg)
        logger.info("Request reply: %s", reply)

    def set_selection(self, session_path: str, mime_types: list[str]) -> None:
        # SetSelection expects a dict with 'mime_types' key
        # In DBus, variant types need to be tuples of (signature, value)
        options = {"mime_types": ("as", mime_types)}
        msg = new_method_call(
            self.address, "SetSelection", "oa{sv}", (session_path, options)
        )
        logger.info("set_selection: %s", msg)
        self.conn.send_and_get_reply(msg)

    def selection_write(self, session_path: str, serial: int) -> int:
        # Returns a file descriptor
        msg = new_method_call(
            self.address, "SelectionWrite", "ou", (session_path, serial)
        )
        logger.info("selection_write: %s", msg)
        reply = self.conn.send_and_get_reply(msg)
        logger.info("selection_write reply: %s", reply)
        # The file descriptor is passed in the ancillary data (fds)
        if reply.fds:
            return reply.fds[0]
        raise RuntimeError("No file descriptor returned from SelectionWrite")

    def selection_write_done(
        self, session_path: str, serial: int, success: bool
    ) -> None:
        msg = new_method_call(
            self.address,
            "SelectionWriteDone",
            "oub",
            (session_path, serial, success),
        )
        logger.info("selection_write: %s", msg)
        self.conn.send_and_get_reply(msg)

    def selection_read(self, session_path: str, mime_type: str) -> int:
        # Returns a file descriptor
        msg = new_method_call(
            self.address, "SelectionRead", "os", (session_path, mime_type)
        )
        reply = self.conn.send_and_get_reply(msg)
        # The file descriptor is passed in the ancillary data (fds)
        if reply.fds:
            return reply.fds[0]
        raise RuntimeError("No file descriptor returned from SelectionRead")

    def receive_selection_owner_changed(self) -> Iterator[dict[str, Any]]:
        """Listen for SelectionOwnerChanged signal events.

        Yields dicts with keys: 'session_path', 'mime_types', 'session_is_owner'.
        """
        # Open a new connection for signal listening
        with open_dbus_connection() as conn:
            match = MatchRule(
                interface=CLIPBOARD_IFACE,
                member="SelectionOwnerChanged",
                path=CLIPBOARD_PATH,
            )
            conn.add_match_rule(match)
            for msg in conn.filter(match):
                # msg.body: (object_path, dict)
                logger.info("owner change: %s", msg)
                session_path, details = msg.body
                # details: {'mime_types': [...], 'session_is_owner': bool}
                yield {
                    "session_path": session_path,
                    "mime_types": details.get("mime_types"),
                    "session_is_owner": details.get("session_is_owner"),
                }

    def receive_selection_transfer(self) -> Iterator[dict[str, Any]]:
        """Listen for SelectionTransfer signal events.

        Yields dicts with keys: 'session_path', 'mime_type', 'serial'.
        """
        with open_dbus_connection() as conn:
            match = MatchRule(
                interface=CLIPBOARD_IFACE,
                member="SelectionTransfer",
                path=CLIPBOARD_PATH,
            )
            conn.add_match_rule(match)
            for msg in conn.filter(match):
                logger.info("selection transfer: %s", msg)
                # msg.body: (object_path, mime_type, serial)
                session_path, mime_type, serial = msg.body
                yield {
                    "session_path": session_path,
                    "mime_type": mime_type,
                    "serial": serial,
                }


# Example usage (sync):
# Copy plain text to the clipboard using the portal API
#
# import os
# import struct
#
# clipboard = Clipboard.new()
# session_path = '/org/freedesktop/portal/desktop/session/1_123/foo'
# mime_types = ['text/plain']
# clipboard.set_selection(session_path, mime_types)
#
# # The portal expects you to write the clipboard data to a file descriptor
# serial = 1  # Serial should be unique per transfer; here we use 1 for demo
# fd = clipboard.selection_write(session_path, serial)
#
# # Write the plain text to the fd (as bytes)
# text = 'Hello from Python!'
# os.write(fd, text.encode('utf-8'))
# os.close(fd)
#
# # Notify the portal that writing is done
# clipboard.selection_write_done(session_path, serial, True)
