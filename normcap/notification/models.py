import enum
from typing import Callable, Optional, Protocol


class HandlerProtocol(Protocol):
    install_instructions: str

    def notify(
        self,
        title: str,
        message: str,
        action_label: Optional[str],
        action_callback: Optional[Callable],
    ) -> bool:
        """Show notification.

        Args:
            title: Title of the notification.
            message: Body of the notification.
            action_label: Button text.
            action_callback: Button action.

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
    """All supported notifcation handlers.

    The handlers are ordered by preference: notify() tries them from top to bottom
    and uses the first one that is detected as compatible.
    """

    # For Linux
    NOTIFY_SEND = enum.auto()

    # For Flatpak
    DBUS_PORTAL = enum.auto()

    # For MacOS and Windows
    QT = enum.auto()
