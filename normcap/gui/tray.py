"""Main entry point for NormCap's UI.

This module hosts most the UI logic. The tray persists from NormCap's start until
the application is closed. Potential windows or other components are started from
here.
"""

import logging
import os
import sys
import time
from enum import Enum
from typing import Any, cast

from PySide6 import QtCore, QtGui, QtWidgets

from normcap import screenshot
from normcap.gui import (
    constants,
    introduction,
    notification_utils,
    permissions_dialog,
    resources,  # noqa: F401 (loads resources!)
    system_info,
    utils,
)
from normcap.gui.dbus_application_service import DBusApplicationService
from normcap.gui.localization import _
from normcap.gui.models import Seconds
from normcap.notification.models import NAME_NOTIFICATION_CLICKED_ACTION

logger = logging.getLogger(__name__)


class TrayIcon(Enum):
    NORMAL = ":tray"
    DONE = ":tray_done"


class SystemTray(QtWidgets.QSystemTrayIcon):
    """System tray icon with menu."""

    def __init__(self, parent: QtCore.QObject, args: dict[str, Any]) -> None:
        logger.debug("System info:\n%s", system_info.to_dict())
        super().__init__(parent)
        self.app = parent

        self.dbus_service = (
            self._get_dbus_service() if system_info.is_flatpak() else None
        )

        # Prepare and connect signals
        self.com = parent.com

        self._set_signals()

        # Prepare instance attributes
        self.screens = parent.screens

        self.installed_languages = parent.installed_languages

        self.settings = parent.settings

        # Setup timers
        # TODO: Handle timers less verbose and init in separate method
        self.reset_tray_icon_timer = QtCore.QTimer(parent=self)
        self.reset_tray_icon_timer.setSingleShot(True)
        self.reset_tray_icon_timer.timeout.connect(self._set_tray_icon_normal)

        self.delayed_exit_timer = QtCore.QTimer(parent=self)
        self.delayed_exit_timer.setSingleShot(True)
        self.delayed_exit_timer.timeout.connect(self.hide)

        self.delayed_init_timer = QtCore.QTimer(parent=self)
        self.delayed_init_timer.setSingleShot(True)
        self.delayed_init_timer.timeout.connect(self.app._delayed_init)
        self.delayed_init_timer.start(50)

        # Prepare UI
        self._set_tray_icon_normal()

        self.tray_menu = QtWidgets.QMenu(None)
        self.tray_menu.aboutToShow.connect(self._populate_context_menu_entries)

        self.setContextMenu(self.tray_menu)
        self._populate_context_menu_entries()

        if args.get("dbus_activation", False):
            # Skip UI setup. Just wait for ActionActivate signal to happen the exit
            self.com.on_action_finished.connect(
                lambda: self.com.on_exit_application.emit(0)
            )
            # Otherwise exit after timeout
            QtCore.QTimer.singleShot(1000, lambda: self.com.on_exit_application.emit(0))
            return

    def _get_dbus_service(self) -> DBusApplicationService | None:
        dbus_service = DBusApplicationService(self.app)
        if not dbus_service.register_service():
            logger.error("Failed to register DBus activation service")
            return None

        logger.debug("Registered DBus activation service")
        return dbus_service

    def _set_tray_icon_normal(self) -> None:
        self.setIcon(QtGui.QIcon(TrayIcon.NORMAL.value))

    @QtCore.Slot()
    def show_introduction(self) -> None:
        show_intro = bool(self.settings.value("show-introduction", type=bool))
        result = introduction.IntroductionDialog(
            show_on_startup=show_intro,
            parent=self.app.windows[0] if self.app.windows else None,
        ).exec()
        if result == introduction.Choice.SHOW:
            self.settings.setValue("show-introduction", True)
        if result == introduction.Choice.DONT_SHOW:
            self.settings.setValue("show-introduction", False)

    @QtCore.Slot()
    def show_permissions_info(self) -> None:
        logger.error("Missing screenshot permission!")
        delay = 0

        if sys.platform == "darwin":
            calling_app = "NormCap" if system_info.is_prebuilt_package() else "Terminal"
            text = constants.PERMISSIONS_TEXT_MACOS.format(application=calling_app)

            # Reset privacy permission in case of new NormCap version. This is necessary
            # because somehow the setting is associated with the binary and won't work
            # after it got updated.
            # TODO: should this be done within has_screenshot_permission?
            screenshot.macos_reset_screenshot_permission()

        elif system_info.is_flatpak():
            text = constants.PERMISSIONS_TEXT_FLATPAK

        elif system_info.display_manager_is_wayland():
            text = constants.PERMISSIONS_TEXT_WAYLAND

        permissions_dialog.PermissionDialog(text=text).exec()
        self.com.on_exit_application.emit(delay)

    @QtCore.Slot()
    def _set_tray_icon_done(self) -> None:
        self.setIcon(QtGui.QIcon(TrayIcon.DONE.value))
        self.reset_tray_icon_timer.start(5000)

    @QtCore.Slot(QtWidgets.QSystemTrayIcon.ActivationReason)
    def _handle_tray_click(
        self, reason: QtWidgets.QSystemTrayIcon.ActivationReason
    ) -> None:
        logger.debug("Tray event: %s", reason)
        if (
            reason == QtWidgets.QSystemTrayIcon.ActivationReason.Trigger
            and self.settings.value("tray", False, type=bool)
        ):
            self.app._show_windows(delay_screenshot=True)

    @QtCore.Slot(str)
    def _apply_setting_change(self, setting: str) -> None:
        if setting == "tray":
            capture_action = self.contextMenu().findChild(QtGui.QAction, name="capture")
            capture_action = cast(QtGui.QAction, capture_action)
            is_tray_visible = bool(self.settings.value(setting, False, type=bool))
            capture_action.setVisible(is_tray_visible)

    def _set_signals(self) -> None:
        """Set up signals to trigger program logic."""
        if self.dbus_service:
            self.dbus_service.action_activated.connect(self._handle_action_activate)
        self.activated.connect(self._handle_tray_click)
        self.com.on_region_selected.connect(self.app._close_windows)
        self.com.on_region_selected.connect(self.app._schedule_detection)
        self.com.on_languages_changed.connect(self.app._sanitize_language_setting)
        self.com.on_languages_changed.connect(self.app._update_installed_languages)
        self.messageClicked.connect(self.app._open_language_manager)

    @QtCore.Slot(str, list)
    def _handle_action_activate(self, action_name: str, parameter: list) -> None:
        if action_name == NAME_NOTIFICATION_CLICKED_ACTION:
            text, text_type = parameter
            notification_utils.perform_action(text=text, text_type=text_type)
            self.com.on_action_finished.emit()

    @QtCore.Slot()
    def _populate_context_menu_entries(self) -> None:
        """Create menu for system tray."""
        self.tray_menu.clear()

        # L10N: Tray menu entry
        action = QtGui.QAction(_("Capture"), self.tray_menu)
        action.setObjectName("capture")
        action.triggered.connect(lambda: self.app._show_windows(delay_screenshot=True))
        action.setVisible(bool(self.settings.value("tray", False, type=bool)))
        self.tray_menu.addAction(action)

        # L10N: Tray menu entry for exiting NormCap completely.
        action = QtGui.QAction(_("Exit"), self.tray_menu)
        action.setObjectName("exit")
        action.triggered.connect(lambda: self.com.on_exit_application.emit(0))
        self.tray_menu.addAction(action)

    @QtCore.Slot()
    def _minimize_or_exit_application(self, delay: Seconds) -> None:
        self.app._close_windows()
        if self.settings.value("tray", type=bool):
            return

        self.com.on_exit_application.emit(delay)

    def hide(self) -> None:
        """Perform last cleanups before quitting application.

        Note: Don't call directly! Instead do `self.com.exit_application.emit(0)`!
        """
        # First call QSystemTrayIcon's method
        super().hide()

        # Leave some time to process final events
        QtWidgets.QApplication.processEvents()
        time.sleep(0.05)

        # Final log messages
        logger.info("Exit normcap")
        logger.debug(
            "Debug images saved in %s%snormcap", utils.tempfile.gettempdir(), os.sep
        )

        # The preferable QApplication.quit() doesn't work reliably on macOS. E.g. when
        # right clicking on "close" in tray menu, NormCap process keeps running.
        # sys.exit(0)
