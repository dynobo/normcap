import logging
from collections.abc import Callable

from PySide6 import QtCore, QtGui, QtWidgets

logger = logging.getLogger(__name__)

install_instructions = "Included out of the box."


def is_compatible() -> bool:
    return True


def is_installed() -> bool:
    return True


def get_qsystem_tray_icon() -> QtWidgets.QSystemTrayIcon:
    """Search for an existing QSystemTrayIcon in the application's children."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        raise RuntimeError("No QApplication instance found.")

    tray = app.findChild(QtWidgets.QSystemTrayIcon)
    if not tray:
        raise RuntimeError("No QSystemTrayIcon instance found.")

    return tray


def notify(
    title: str,
    message: str,
    action_label: str | None = None,
    action_callback: Callable | None = None,
) -> bool:
    """Send via QSystemTrayIcon.

    Doesn't support an action label, but triggers action on notification clicked.

    Used for:
        - Windows
        - macOS
        - Linux (Fallback in case no notify-send)

    On Linux, this method has draw backs (probably Qt Bugs):
        - The custom icon is ignored. Instead the default icon
          `QtWidgets.QSystemTrayIcon.MessageIcon.Information` is shown.
        - Notifications clicks are not received. It _does_ work, if
          `QtWidgets.QSystemTrayIcon.MessageIcon.Critical` is used as icon.
    """
    logger.debug("Send notification via QT")

    tray = get_qsystem_tray_icon()

    # Because clicks on different notifications can not be distinguished in Qt,
    # only the last notification is associated with an action/signal. All previous
    # get removed.
    if tray.isSignalConnected(QtCore.QMetaMethod.fromSignal(tray.messageClicked)):
        tray.messageClicked.disconnect()

    # Only act on notification clicks, if we have an action.
    if action_callback is not None:
        tray.messageClicked.connect(action_callback)

    tray.show()
    tray.showMessage(title, message, QtGui.QIcon(":notification"))

    return True
