import logging
from typing import Callable

from normcap.notification.models import Handler, HandlerProtocol

from .handlers import dbus_portal, notify_send, qt

logger = logging.getLogger(__name__)


_notification_handlers: dict[Handler, HandlerProtocol] = {
    Handler.DBUS_PORTAL: dbus_portal,
    Handler.NOTIFY_SEND: notify_send,
    Handler.QT: qt,
}


def get_available_handlers() -> list[Handler]:
    compatible_handlers = [
        h for h in Handler if _notification_handlers[h].is_compatible()
    ]
    logger.debug(
        "Compatible capture handlers: %s", [h.name for h in compatible_handlers]
    )

    available_handlers = [
        n for n in compatible_handlers if _notification_handlers[n].is_installed()
    ]
    logger.debug("Available capture handlers: %s", [h.name for h in available_handlers])

    if not compatible_handlers:
        logger.error(
            "None of the implemented capture handlers is compatible with this system!"
        )
        return []

    if not available_handlers:
        logger.error(
            "No working capture handler found for your system. "
            "The preferred handler on your system would be %s but can't be "
            "used due to missing dependencies. %s",
            compatible_handlers[0].name,
            _notification_handlers[compatible_handlers[0]].install_instructions,
        )
        return []

    if compatible_handlers[0] != available_handlers[0]:
        logger.warning(
            "The preferred capture handler on your system would be %s but can't be "
            "used due to missing dependencies. %s",
            compatible_handlers[0].name,
            _notification_handlers[compatible_handlers[0]].install_instructions,
        )

    return available_handlers


def _notify(
    handler: Handler,
    title: str,
    message: str,
    action_label: str,
    action_callback: Callable,
) -> bool:
    notification_handler = _notification_handlers[handler]
    if not notification_handler.is_compatible():
        logger.warning("%s's notify() called on incompatible system!", handler.name)
    try:
        notification_handler.notify(
            title=title,
            message=message,
            action_label=action_label,
            action_callback=action_callback,
        )
    except Exception:
        logger.exception("%s's notify() failed!", handler.name)
        return False

    logger.info("Notification send using %s", handler.name)
    return True


def notify_with_handler(
    handler_name: str,
    title: str,
    message: str,
    action_label: str,
    action_callback: Callable,
) -> bool:
    """Send desktop notification using a specific handler."""
    return _notify(
        handler=Handler[handler_name.upper()],
        title=title,
        message=message,
        action_label=action_label,
        action_callback=action_callback,
    )


def notify(
    title: str,
    message: str,
    action_label: str,
    action_callback: Callable,
) -> None:
    """Send desktop notification using compatible handlers."""
    for handler in get_available_handlers():
        if _notify(
            handler=handler,
            title=title,
            message=message,
            action_label=action_label,
            action_callback=action_callback,
        ):
            return

    logger.error("Unable to capture screen! (Increase log-level for details)")
