import functools
import logging

from .handlers import base, pbcopy, qtclipboard, windll, wlclipboard, xclip

logger = logging.getLogger(__name__)

clipboard_handlers: list[type[base.ClipboardHandlerBase]] = [
    windll.WindllHandler,  # win32
    pbcopy.PbCopyHandler,  # darwin
    xclip.XclipCopyHandler,  # linux, should work on wayland
    wlclipboard.WlCopyHandler,  # linux, should work on wayland, broken in Gnome 45 atm
    qtclipboard.QtCopyHandler,  # cross platform
]

# TODO: Think about implementing a _real_ success check
#       by implementing "read from clipboard" for all handlers and check if the text can
#       be retrieved from clipboard after copy().


@functools.cache
def get_compatible_handlers() -> list[base.ClipboardHandlerBase]:
    """Retrieve all handlers which are likely to work on the given system.

    Returns:
        Instances of all compatible clipboard handlers.
    """
    instances = [handler() for handler in clipboard_handlers]
    return [i for i in instances if i.is_compatible]


def has_compatible_handler() -> bool:
    """Check if the system supports one (or more) of the implemented clipboard handlers.

    Returns:
        If system is supported.
    """
    return len(get_compatible_handlers()) > 0


def copy(text: str) -> bool:
    """Copy text to system clipboard.

    Args:
        text: Text to be copied.

    Returns:
        If an error has occurred and the text likely was not copied correctly.
    """
    for copy in get_compatible_handlers():
        result = copy.copy(text)
        if result:
            logger.debug("Text copied to clipboard using %s.", copy.name)
            return True
        logger.warning(
            "Strategy '%s' should be compatible but did not work!", copy.name
        )

    logger.error("Unable to copy text to clipboard! (Increase log-level for details)")
    return False
