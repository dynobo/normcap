"""Python equivalent of the Rust Session struct for DBus portal sessions.

using jeepney for DBus interaction.
"""

from typing import Any, Optional

from jeepney import DBusAddress, MessageType, new_method_call
from jeepney.io.blocking import open_dbus_connection

SessionDetails = dict[str, Any]


class Session:
    """Wrapper for the org.freedesktop.portal.Session DBus interface.

    Synchronous version using jeepney.
    """

    INTERFACE = "org.freedesktop.portal.Session"

    def __init__(self, object_path: str) -> None:
        self.object_path = object_path
        self.address = DBusAddress(
            object_path=object_path,
            bus_name="org.freedesktop.portal.Desktop",
            interface=self.INTERFACE,
        )
        self.conn = open_dbus_connection()

    @classmethod
    def from_handle_token(cls, handle_token: str) -> "Session":
        # This is a placeholder for the logic to construct the object path from a
        # handle token.
        # The actual logic may depend on your application's conventions.
        path = f"/org/freedesktop/portal/desktop/session/{handle_token}"
        return cls(path)

    def receive_closed(self) -> Optional[SessionDetails]:
        """Listen for the 'Closed' signal.

        This is a blocking call that waits for the signal.
        Returns the details dict from the signal, or None if interrupted.
        """
        # Listen for the 'Closed' signal on this session's object path
        for msg in self.conn.filter(
            messages=[
                {
                    "type": MessageType.signal,
                    "interface": self.INTERFACE,
                    "member": "Closed",
                    "path": self.object_path,
                }
            ]
        ):
            if msg.header.member == "Closed":
                # The signal's body is a tuple with one dict argument
                details = msg.body[0] if msg.body else {}
                return details
        return None

    def close(self) -> None:
        """Call the 'Close' method on the session."""
        call = new_method_call(self.address, "Close", signature="", body=())
        self.conn.send_and_get_reply(call)

    def path(self) -> str:
        return self.object_path

    def __repr__(self) -> str:
        return f"<Session path={self.object_path}>"


# Example usage:
#
# from dbus_session import Session
#
# # Create a session from a handle token (replace with your actual token)
# session = Session.from_handle_token("your_handle_token")
#
# # Close the session
# session.close()
#
# # Wait for the session to be closed (blocking)
# details = session.receive_closed()
# print("Session closed with details:", details)
