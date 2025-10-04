import enum
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

ACTION_NAME_NOTIFICATION_CLICKED = "notification_clicked"


@dataclass
class NotificationAction:
    label: str
    func: Callable
    args: list[tuple[str, str]] | None


class HandlerProtocol(Protocol):
    install_instructions: str

    def notify(
        self,
        title: str,
        message: str,
        actions: list[NotificationAction] | None,
    ) -> bool:
        """Show notification.

        Args:
            title: Title of the notification.
            message: Body of the notification.
            actions: List of actions which the user can trigger through notification.
                Note: Not all handlers support (multiple) notification.

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

    # For Flatpak
    DBUS_PORTAL = enum.auto()

    # For Linux
    NOTIFY_SEND = enum.auto()

    # For MacOS and Windows
    QT = enum.auto()
