"""Hacks for moving windows to a certain screen on Wayland."""

import logging

from PySide6 import QtWidgets

from normcap.gui.constants import URLS  # TODO: Remove
from normcap.positioning.handlers import kscript, window_calls
from normcap.positioning.models import Handler, HandlerProtocol
from normcap.system.models import Screen

logger = logging.getLogger(__name__)


_positioning_handlers: dict[Handler, HandlerProtocol] = {
    Handler.WINDOW_CALLS: window_calls,
    # TODO: Add Window Calls Extended handler
    Handler.KSCRIPT: kscript,
}


def get_available_handlers() -> list[Handler]:
    compatible_handlers = [
        h for h in Handler if _positioning_handlers[h].is_compatible()
    ]
    logger.debug(
        "Compatible positioning handlers: %s", [h.name for h in compatible_handlers]
    )

    available_handlers = [
        n for n in compatible_handlers if _positioning_handlers[n].is_installed()
    ]
    logger.debug(
        "Available positioning handlers: %s", [h.name for h in available_handlers]
    )

    if not compatible_handlers:
        logger.error(
            "None of the implemented window positioning handlers is compatible with "
            "this system!"
        )
        return []

    if not available_handlers:
        logger.error(
            "No working window positioning handler found for your system. "
            "The preferred handler on your system would be %s but can't be "
            "used due to missing dependencies. %s",
            compatible_handlers[0].name,
            _positioning_handlers[compatible_handlers[0]].install_instructions,
        )
        return []

    if compatible_handlers[0] != available_handlers[0]:
        logger.warning(
            "The preferred window positioning handler on your system would be %s but "
            "can't be used due to missing dependencies. %s",
            compatible_handlers[0].name,
            _positioning_handlers[compatible_handlers[0]].install_instructions,
        )

    return available_handlers


def _move(handler: Handler, window: QtWidgets.QMainWindow, screen: Screen) -> None:
    positioning_handler = _positioning_handlers[handler]
    if not positioning_handler.is_compatible():
        logger.warning("%s's position() called on incompatible system!", handler.name)
    try:
        positioning_handler.move(window=window, screen=screen)
    except Exception:
        logger.exception("%s's position() failed!", handler.name)
    else:
        logger.info("Window positioned using %s", handler.name)


def move_with_handler(
    handler_name: str, window: QtWidgets.QMainWindow, screen: Screen
) -> None:
    """Position window on screen using a specific handler.

    Args:
        handler_name: Name of one of the supported capture methods.
        window: Qt Window to be re-positioned.
        screen: Geometry of the target screen.

    Returns:
        Single image for every screen.
    """
    _move(handler=Handler[handler_name.upper()], window=window, screen=screen)


def move(window: QtWidgets.QMainWindow, screen: Screen) -> None:
    """Position window on screen using best compatible handler.

    Args:
        window: Qt Window to be re-positioned.
        screen: Geometry of the target screen.
    """
    for handler in get_available_handlers():
        _move(handler=handler, window=window, screen=screen)
        return

    logger.error(
        "Unable to to position window! "
        "This is ususally no probem when NormCap is used with a single monitor. "
        "But in multi monitor setups, it likely causes window displacments which "
        "can practically make NormCap unusable. "
        "Consider reporting your report issue: %s",
        URLS.issues,
    )
