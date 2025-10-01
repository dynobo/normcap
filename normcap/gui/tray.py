"""Main entry point for NormCap's UI.

This module hosts most the UI logic. The tray persists from NormCap's start until
the application is closed. Potential windows or other components are started from
here.
"""

import logging
from enum import Enum
from typing import cast

from PySide6 import QtCore, QtGui, QtWidgets

from normcap.gui import resources  # noqa: F401 (loads resources!)
from normcap.gui.localization import _

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

    def __init__(self, parent: QtCore.QObject, keep_in_tray: bool) -> None:
        super().__init__(parent)
        self.keep_in_tray = keep_in_tray

        # Prepare and connect signals
        self.com = Communicate()

        # Prepare UI
        self._set_icon(icon=Icon.NORMAL)
        self.tray_menu = self._create_context_menu()
        self.setContextMenu(self.tray_menu)

        # Connect signals
        self.activated.connect(self._handle_activated)
        self.messageClicked.connect(lambda: self.com.on_notification_clicked.emit())
        self.tray_menu.aboutToShow.connect(self._update_context_menu_entries)

        # Setup timer
        self.reset_icon_timer = QtCore.QTimer(parent=self, singleShot=True)
        self.reset_icon_timer.timeout.connect(lambda: self._set_icon(Icon.NORMAL))

    def _set_icon(self, icon: Icon) -> None:
        self.setIcon(QtGui.QIcon(icon.value))

    @QtCore.Slot()
    def _show_completion_icon(self) -> None:
        self._set_icon(icon=Icon.DONE)
        self.reset_icon_timer.start(5000)

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
        """Create menu for system tray."""
        capture_action = self.contextMenu().findChild(QtGui.QAction, name="capture")
        capture_action.setVisible(self.keep_in_tray)

    def _create_context_menu(self) -> QtWidgets.QMenu:
        """Create menu for system tray."""
        tray_menu = QtWidgets.QMenu(None)

        # L10N: Tray menu entry
        action = QtGui.QAction(_("Capture"), tray_menu)
        action.setObjectName("capture")
        action.triggered.connect(self.com.on_menu_capture_clicked.emit)
        action.setVisible(self.keep_in_tray)
        tray_menu.addAction(action)

        # L10N: Tray menu entry for exiting NormCap completely.
        action = QtGui.QAction(_("Exit"), tray_menu)
        action.setObjectName("exit")
        action.triggered.connect(self.com.on_menu_exit_clicked.emit)
        tray_menu.addAction(action)
        return tray_menu

    def apply_setting_change(self, setting: str, value: bool | str | int) -> None:
        if setting == "tray":
            capture_action = self.contextMenu().findChild(QtGui.QAction, name="capture")
            capture_action = cast(QtGui.QAction, capture_action)
            self.keep_in_tray = bool(value)
            capture_action.setVisible(self.keep_in_tray)
