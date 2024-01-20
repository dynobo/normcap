import logging

from PySide6 import QtGui

from normcap.screengrab.handlers import dbus_portal, dbus_shell, grim, qt
from normcap.screengrab.structures import Handler, HandlerProtocol

logger = logging.getLogger(__name__)


_capture_handlers: dict[Handler, HandlerProtocol] = {
    Handler.QT: qt,
    Handler.DBUS_PORTAL: dbus_portal,
    Handler.DBUS_SHELL: dbus_shell,
    Handler.GRIM: grim,
}


def get_available_handlers() -> list[Handler]:
    compatible_handlers = [h for h in Handler if _capture_handlers[h].is_compatible()]
    logger.debug(
        "Compatible capture handlers: %s", [h.name for h in compatible_handlers]
    )

    available_handlers = [
        n for n in compatible_handlers if _capture_handlers[n].is_installed()
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
            _capture_handlers[compatible_handlers[0]].install_instructions,
        )
        return []

    if compatible_handlers[0] != available_handlers[0]:
        logger.warning(
            "The preferred capture handler on your system would be %s but can't be "
            "used due to missing dependencies. %s",
            compatible_handlers[0].name,
            _capture_handlers[compatible_handlers[0]].install_instructions,
        )

    return available_handlers


def _capture(handler: Handler) -> list[QtGui.QImage]:
    capture_handler = _capture_handlers[handler]
    if not capture_handler.is_compatible():
        logger.warning("%s's capture() called on incompatible system!", handler.name)
    try:
        images = capture_handler.capture()
    except Exception:
        logger.exception("%s's capture() failed!", handler.name)
        return []
    else:
        logger.info("Screen captured using %s", handler.name)
        return images


def capture_with_handler(handler_name: str) -> list[QtGui.QImage]:
    """Capture screen using a specific handler.

    Args:
        handler_name: Name of one of the supported capture methods.

    Returns:
        Single image for every screen.
    """
    return _capture(handler=Handler[handler_name.upper()])


def capture() -> list[QtGui.QImage]:
    """Capture screen using compatible handlers.

    Returns:
        Single image for every screen.
    """
    for handler in get_available_handlers():
        if images := _capture(handler=handler):
            return images

    logger.error("Unable to capture screen! (Increase log-level for details)")
    return []
