import logging
from typing import Callable, Optional

from PySide6 import QtDBus

from normcap.gui import system_info

logger = logging.getLogger(__name__)

install_instructions = ""

DESKTOP_SERVICE = "org.freedesktop.portal.Desktop"
DESKTOP_PATH = "/org/freedesktop/portal/desktop"
NOTIFICATION_INTERFACE = "org.freedesktop.portal.Notification"
INTROSPECTABLE_SERVICE = "org.freedesktop.DBus.Introspectable"


def is_compatible() -> bool:
    return system_info.is_flatpak_package()


def is_installed() -> bool:
    session_bus = QtDBus.QDBusConnection.sessionBus()
    if not session_bus.isConnected():
        logger.warning("Cannot connect to the DBus session bus.")
        return False

    iface = QtDBus.QDBusInterface(
        DESKTOP_SERVICE,
        DESKTOP_PATH,
        INTROSPECTABLE_SERVICE,
        session_bus,
    )
    if not iface.isValid():
        logger.warning(
            "DBus Notification is invalid: %s", session_bus.lastError().message()
        )
        return False

    message = iface.call("Introspect")
    reply = QtDBus.QDBusReply(message)
    if not reply.isValid():
        error = reply.error().message()
        logger.warning("Cannot introspect DBus: %s", error)
        return False

    value = reply.value()
    return NOTIFICATION_INTERFACE in value


def notify(
    title: str,
    message: str,
    action_label: Optional[str] = None,
    action_callback: Optional[Callable] = None,
) -> bool:
    bus = QtDBus.QDBusConnection.sessionBus()
    if not bus.isConnected():
        return False

    notification_app_id = "com.github.dynobo.normcap"
    notification_data = {
        "title": title,
        "body": message,
    }

    # if action_label and action_callback:
    #     notification_data["buttons"] = [{"label": action_label, "action": "default"}]

    # Send the notification
    dbus_message = QtDBus.QDBusMessage.createMethodCall(
        DESKTOP_SERVICE,
        DESKTOP_PATH,
        NOTIFICATION_INTERFACE,
        "AddNotification",
    )

    dbus_message.setArguments([notification_app_id, notification_data])

    if not bus.send(dbus_message):
        logger.error("Failed to send notification!")
        return False

    # Handle the action callback
    # if action_label and action_callback:

    #     def handle_action_reply(reply_message: QtDBus.QDBusMessage):
    #         if reply_message.arguments() and reply_message.arguments()[0] == "TODO":
    #             action_callback()

    #     bus.connect(
    #         notification_service,
    #         notification_path,
    #         notification_interface,
    #         "ActionInvoked",
    #         handle_action_reply,
    #     )

    return True
