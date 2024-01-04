import logging
from enum import Enum

from .handlers import pbcopy, qtclipboard, windll, wlclipboard, xclip

logger = logging.getLogger(__name__)


class ClipboardHandlers(Enum):
    """All supported clipboard handlers.

    The handlers are ordered by preference: copy() tries them from top to bottom
    and uses the first one that is detected as compatible.
    """

    # For win32
    windll = windll.WindllHandler()

    # For darwin
    pbcopy = pbcopy.PbCopyHandler()

    # Cross platform
    # - Not working on linux with wayland
    qt = qtclipboard.QtCopyHandler()

    # For linux with wayland
    # - Not working with Awesome WM
    # - Problems with Gnome 45: https://github.com/bugaevc/wl-clipboard/issues/168
    wlclipboard = wlclipboard.WlCopyHandler()

    # For linux with xorg and wayland
    # - Seems not very robust on wayland
    # - Works with Awesome WM
    xclip = xclip.XclipCopyHandler()


# TODO: Think about implementing a _real_ success check
#       by implementing "read from clipboard" for all handlers and check if the text can
#       be retrieved from clipboard after copy().


def copy_with_handler(text: str, handler_name: str) -> bool:
    """Copy text to system clipboard using a specific handler.

    Args:
        text: Text to be copied.
        handler_name: Name of one of the supported clipboard methods.

    Returns:
        If an error has occurred and the text likely was not copied correctly.
    """
    handler = ClipboardHandlers[handler_name].value
    result = handler.copy(text)

    if result:
        logger.debug("Text copied to clipboard using '%s.' handler", handler_name)
        return True

    logger.warning("Clipboard handler '%s' did not succeed!", handler_name)
    return False


def copy(text: str) -> bool:
    """Copy text to system clipboard using compatible handlers.

    Args:
        text: Text to be copied.

    Returns:
        If an error has occurred and the text likely was not copied correctly.
    """
    for handler in ClipboardHandlers:
        if not handler.value.is_compatible:
            logger.debug("Skipping incompatible clipboard handler '%s'", handler.name)
            continue

        if copy_with_handler(text=text, handler_name=handler.name):
            return True

    logger.error("Unable to copy text to clipboard! (Increase log-level for details)")
    return False
