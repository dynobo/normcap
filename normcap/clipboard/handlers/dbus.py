import logging
import os
import random

from normcap.clipboard import system_info
from normcap.clipboard.handlers.dbus_clipboard import Clipboard
from normcap.clipboard.handlers.dbus_session import Session

logger = logging.getLogger(__name__)


install_instructions = (
    "Please install the package 'xclip' with your system's package manager."
)


def copy(text: str) -> None:
    """Use xclip package to copy text to system clipboard."""
    random_str = "".join(random.choice("abcdefghi") for _ in range(8))  # noqa: S311
    session = Session.from_handle_token(f"normcap_{random_str}")
    logger.debug("session: %s", session)

    clipboard = Clipboard.new()

    clipboard.request(session.path())

    mime_types = ["text/plain"]
    clipboard.set_selection(session.path(), mime_types)

    # The portal expects you to write the clipboard data to a file descriptor
    serial = 1  # Serial should be unique per transfer; here we use 1 for demo
    fd = clipboard.selection_write(session.path(), serial)
    logger.debug("fd: %s", fd)

    # Write the plain text to the fd (as bytes)
    text = "Hello from Python!"
    os.write(fd, text.encode("utf-8"))
    os.close(fd)

    clipboard.selection_write_done(
        session_path=session.path(), serial=serial, success=True
    )


def is_compatible() -> bool:
    return system_info.is_flatpak_package()


def is_installed() -> bool:
    return system_info.is_flatpak_package()
