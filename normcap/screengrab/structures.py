import enum
from typing import Protocol

from PySide6 import QtGui


class HandlerProtocol(Protocol):
    install_instructions: str

    def capture(self) -> list[QtGui.QImage]:
        """Copy text to system clipboard.

        Returns:
            Single image for every screen.
        """
        ...  # pragma: no cover

    def is_compatible(self) -> bool:
        """Check if the system theoretically could to use this method.

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
    """All supported screengrab handlers.

    The handlers are ordered by preference: capture() tries them from top to bottom
    and uses the first one that is detected as compatible.
    """

    # Cross platform, but not working on linux with wayland
    QT = enum.auto()

    # For linux with wayland but without dbus portal, e.g. Hyprland
    GRIM = enum.auto()

    # For linux with wayland
    DBUS_PORTAL = enum.auto()

    # For linux with wayland, old variant, e.g. for Ubuntu 20.04
    DBUS_SHELL = enum.auto()
