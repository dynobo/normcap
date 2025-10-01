"""Main entry point for NormCap's UI.

This module hosts most the UI logic. The tray persists from NormCap's start until
the application is closed. Potential windows or other components are started from
here.
"""

import logging
from enum import Enum

from PySide6 import QtCore, QtGui, QtWidgets

from normcap.gui import resources  # noqa: F401 (loads resources!)
from normcap.gui.localization import _
from normcap.gui.models import Seconds

logger = logging.getLogger(__name__)


class Icon(Enum):
    NORMAL = ":tray"
    DONE = ":tray_done"


class Communicate(QtCore.QObject):
    """System Tray's communication bus."""

    on_notification_clicked = QtCore.Signal()
    on_tray_clicked = QtCore.Signal()
    on_menu_capture_clicked = QtCore.Signal()
    on_menu_exit_clicked = QtCore.Signal()


class SystemTray(QtWidgets.QSystemTrayIcon):
    """System tray icon with menu."""

    _ICON_RESET_TIMEOUT: Seconds = 5

    def __init__(self, parent: QtCore.QObject, keep_in_tray: bool) -> None:
        super().__init__(parent)
        self.keep_in_tray = keep_in_tray

        self.com = Communicate()

        self.set_icon(icon=Icon.NORMAL)
        self.tray_menu = self._create_context_menu()
        self.setContextMenu(self.tray_menu)

        self._connect_signals()

    def _connect_signals(self) -> None:
        self.activated.connect(self._handle_activated)
        self.messageClicked.connect(lambda: self.com.on_notification_clicked.emit())
        self.tray_menu.aboutToShow.connect(self._update_context_menu_entries)

    def set_icon(self, icon: Icon) -> None:
        self.setIcon(QtGui.QIcon(icon.value))

    def show_completion_icon(self) -> None:
        self.set_icon(icon=Icon.DONE)
        QtCore.QTimer.singleShot(
            int(self._ICON_RESET_TIMEOUT * 1000), lambda: self.set_icon(Icon.NORMAL)
        )

    def _handle_activated(
        self, reason: QtWidgets.QSystemTrayIcon.ActivationReason
    ) -> None:
        logger.debug("Tray event: %s", reason)
        if (
            reason == QtWidgets.QSystemTrayIcon.ActivationReason.Trigger
            and self.keep_in_tray
        ):
            self.com.on_tray_clicked.emit()

    def _update_context_menu_entries(self) -> None:
        """Update menu entries visibility based on current settings."""
        self.capture_action.setVisible(self.keep_in_tray)

    def _create_context_menu(self) -> QtWidgets.QMenu:
        """Create menu for system tray."""
        tray_menu = QtWidgets.QMenu(None)

        # L10N: Tray menu entry
        self.capture_action = QtGui.QAction(_("Capture"), tray_menu)
        self.capture_action.setObjectName("capture")
        self.capture_action.triggered.connect(self.com.on_menu_capture_clicked.emit)
        self.capture_action.setVisible(self.keep_in_tray)
        tray_menu.addAction(self.capture_action)

        # L10N: Tray menu entry for exiting NormCap completely.
        self.exit_action = QtGui.QAction(_("Exit"), tray_menu)
        self.exit_action.setObjectName("exit")
        self.exit_action.triggered.connect(self.com.on_menu_exit_clicked.emit)
        tray_menu.addAction(self.exit_action)
        return tray_menu

    def apply_setting_change(self, setting: str, value: bool | str | int) -> None:
        """Propagate setting changes to the UI."""
        if setting == "tray":
            self.keep_in_tray = bool(value)
            self.capture_action.setVisible(self.keep_in_tray)
