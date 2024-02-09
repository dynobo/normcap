import logging

from normcap.clipboard.structures import Handler, HandlerProtocol

from .handlers import pbcopy, qtclipboard, windll, wlclipboard, xclip, xsel

logger = logging.getLogger(__name__)


# TODO: Think about implementing a _real_ success check
#       by implementing "read from clipboard" for all handlers and check if the text can
#       be retrieved from clipboard after copy().


_clipboard_handlers: dict[Handler, HandlerProtocol] = {
    Handler.WINDLL: windll,
    Handler.PBCOPY: pbcopy,
    Handler.QT: qtclipboard,
    Handler.WLCLIPBOARD: wlclipboard,
    Handler.XSEL: xsel,
    Handler.XCLIP: xclip,
}


def _copy(text: str, handler: Handler) -> bool:
    clipboard_handler = _clipboard_handlers[handler]
    if not clipboard_handler.is_compatible():
        logger.warning("%s's copy() called on incompatible system!", handler.name)
    try:
        clipboard_handler.copy(text=text)
    except Exception:
        logger.exception("%s's copy() failed!", handler.name)
        return False
    else:
        logger.info("Text copied to clipboard using %s", handler.name)
        return True


def copy_with_handler(text: str, handler_name: str) -> bool:
    """Copy text to system clipboard using a specific handler.

    Args:
        text: Text to be copied.
        handler_name: Name of one of the supported clipboard methods.

    Returns:
        If an error has occurred and the text likely was not copied correctly.
    """
    return _copy(text=text, handler=Handler[handler_name.upper()])


def copy(text: str) -> bool:
    """Copy text to system clipboard using compatible handlers.

    Args:
        text: Text to be copied.

    Returns:
        False, if an error has occurred and the text likely was not copied correctly.
        True, if no error occurred. Note that this is no guarantee that the text was
        actually copied, as it still depends on system capabilities.
    """
    for handler in get_available_handlers():
        if _copy(text=text, handler=handler):
            return True

    logger.error("Unable to copy text to clipboard! (Increase log-level for details)")
    return False


def get_available_handlers() -> list[Handler]:
    compatible_handlers = [h for h in Handler if _clipboard_handlers[h].is_compatible()]
    logger.debug(
        "Compatible clipboard handlers: %s", [h.name for h in compatible_handlers]
    )

    available_handlers = [
        n for n in compatible_handlers if _clipboard_handlers[n].is_installed()
    ]
    logger.debug(
        "Available clipboard handlers: %s", [h.name for h in available_handlers]
    )

    if not compatible_handlers:
        logger.error(
            "None of the implemented clipboard handlers is compatible with this system!"
        )
        return []

    if not available_handlers:
        logger.error(
            "No working clipboard handler found for your system. "
            "The preferred handler on your system would be %s but can't be "
            "used due to missing dependencies. %s",
            compatible_handlers[0].name,
            _clipboard_handlers[compatible_handlers[0]].install_instructions,
        )
        return []

    if compatible_handlers[0] != available_handlers[0]:
        logger.warning(
            "The preferred clipboard handler on your system would be %s but can't be "
            "used due to missing dependencies. %s",
            compatible_handlers[0].name,
            _clipboard_handlers[compatible_handlers[0]].install_instructions,
        )

    return available_handlers
