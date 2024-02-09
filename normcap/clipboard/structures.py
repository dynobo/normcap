import enum
from typing import Protocol


class HandlerProtocol(Protocol):
    install_instructions: str

    def copy(self, text: str) -> None:
        """Copy text to system clipboard.

        Args:
            text: Text to be copied.

        Returns:
            False, if an error has occurred.
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
    """All supported clipboard handlers.

    The handlers are ordered by preference: copy() tries them from top to bottom
    and uses the first one that is detected as compatible.
    """

    # For win32
    WINDLL = enum.auto()

    # For darwin
    PBCOPY = enum.auto()

    # Cross platform
    # - Not working on linux with wayland
    QT = enum.auto()

    # For linux with wayland
    # - Not working with Awesome WM
    # - Problems with Gnome 45: https://github.com/bugaevc/wl-clipboard/issues/168
    WLCLIPBOARD = enum.auto()

    # For linux with xorg or wayland
    # - Seems to work a bit more robust on wayland than xclip
    XSEL = enum.auto()

    # For linux with xorg or wayland
    # - Seems not very robust on wayland
    # - Seems not to work from within Flatpak ("Display not found")
    # - Works with Awesome WM
    XCLIP = enum.auto()
