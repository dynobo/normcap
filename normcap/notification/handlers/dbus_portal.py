import logging
from collections.abc import Callable

from jeepney.io.blocking import Proxy, open_dbus_connection
from jeepney.wrappers import MessageGenerator, new_method_call

from normcap.gui import system_info

logger = logging.getLogger(__name__)

install_instructions = ""

DESKTOP_SERVICE = "org.freedesktop.portal.Desktop"
DESKTOP_PATH = "/org/freedesktop/portal/desktop"
NOTIFICATION_INTERFACE = "org.freedesktop.portal.Notification"
INTROSPECTABLE_SERVICE = "org.freedesktop.DBus.Introspectable"


class DBusNotificationPortal(MessageGenerator):
    """jeepney MessageGenerator for the notification portal."""

    interface = NOTIFICATION_INTERFACE

    def __init__(
        self,
        object_path: str = DESKTOP_PATH,
        bus_name: str = DESKTOP_SERVICE,
    ) -> None:
        super().__init__(object_path=object_path, bus_name=bus_name)

    def add_notification(self, app_id: str, notification_data: dict) -> object:
        return new_method_call(
            self, "AddNotification", "sa{sv}", (app_id, notification_data)
        )


class DBusIntrospectable(MessageGenerator):
    """jeepney MessageGenerator for introspection."""

    interface = INTROSPECTABLE_SERVICE

    def __init__(
        self,
        object_path: str = DESKTOP_PATH,
        bus_name: str = DESKTOP_SERVICE,
    ) -> None:
        super().__init__(object_path=object_path, bus_name=bus_name)

    def introspect(self) -> object:
        return new_method_call(self, "Introspect")


def is_compatible() -> bool:
    return system_info.is_flatpak()


def is_installed() -> bool:
    """Check if the DBus notification portal is available.

    Returns:
        True if the portal is available, False otherwise
    """
    try:
        with open_dbus_connection() as connection:
            proxy = Proxy(DBusIntrospectable(), connection)
            xml_response = proxy.introspect()[0]

            if not isinstance(xml_response, str):
                logger.warning("Invalid introspection response: %s", xml_response)
                return False

            return NOTIFICATION_INTERFACE in xml_response

    except Exception as exc:
        logger.warning("Cannot introspect DBus: %s", exc)
        return False


def notify(
    title: str,
    message: str,
    action_label: str | None = None,
    action_callback: Callable | None = None,
) -> bool:
    """Send a notification via the DBus portal.

    Note: For flatpak applications, notification actions are limited.
    This implementation sends a simple notification that activates the app
    when clicked, but doesn't support custom action buttons reliably.

    Args:
        title: Notification title
        message: Notification message body
        action_label: Optional label for action button (ignored for now)
        action_callback: Optional callback (not used directly but required
                         for interface compatibility)

    Returns:
        True if notification was sent successfully, False otherwise
    """
    try:
        with open_dbus_connection() as connection:
            proxy = Proxy(DBusNotificationPortal(), connection)

            notification_app_id = "com.github.dynobo.normcap"
            notification_data: dict[str, tuple[str, object]] = {
                "title": ("s", title),
                "body": ("s", message),
                "default-action": ("s", "activate"),
            }

            proxy.add_notification(notification_app_id, notification_data)
            return True

    except Exception:
        logger.exception("Failed to send notification")
        return False
