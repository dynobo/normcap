import enum
from typing import Protocol

from PySide6 import QtWidgets

from normcap.platform.models import Screen


class HandlerProtocol(Protocol):
    install_instructions: str

    def move(self, window: QtWidgets.QMainWindow, screen: Screen) -> None:
        """Position window on screen."""
        ...  # pragma: no cover

    def is_compatible(self) -> bool:
        """Check if the system theoretically could use this method.

        Returns:
            System could be capable of using this method
        """
        ...  # pragma: no cover

    def is_installed(self) -> bool:
        """Check if the dependencies (binaries) for this method are available.

        Returns:
            System has all necessary dependencies
        """
        ...  # pragma: no cover


class Handler(enum.IntEnum):
    """All supported positioning handlers.

    The handlers are ordered by preference: move() tries them from top to bottom
    and uses the first one that is detected as compatible.
    """

    # Preferable on Wayland + Gnome
    WINDOW_CALLS = enum.auto()

    # Might work on some Wayland + KDE. The newer the system, the less likely to work.
    KSCRIPT = enum.auto()
