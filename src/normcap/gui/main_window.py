"""Normcap main window."""
import os
import tempfile
import time
from typing import Dict, Tuple

from PySide2 import QtCore, QtGui, QtWidgets

from normcap import clipboard
from normcap.enhance import enhance_image
from normcap.gui.base_window import BaseWindow
from normcap.gui.notifier import Notifier
from normcap.gui.settings import init_settings, log_settings
from normcap.gui.settings_menu import SettingsMenu
from normcap.gui.system_tray import SystemTray
from normcap.gui.update_check import UpdateChecker
from normcap.logger import logger
from normcap.magic import apply_magic
from normcap.models import (
    FILE_ISSUE_TEXT,
    Capture,
    CaptureMode,
    DesktopEnvironment,
    DisplayManager,
    Platform,
    Rect,
    SystemInfo,
)
from normcap.ocr import perform_ocr
from normcap.screengrab import grab_screen
from normcap.utils import set_cursor


class Communicate(QtCore.QObject):
    """Applications' communication bus."""

    on_region_selected = QtCore.Signal(Rect)
    on_image_grabbed = QtCore.Signal()
    on_ocr_performed = QtCore.Signal()
    on_image_prepared = QtCore.Signal()
    on_copied_to_clipboard = QtCore.Signal()
    on_send_notification = QtCore.Signal(Capture)
    on_window_positioned = QtCore.Signal()
    on_minimize_windows = QtCore.Signal()
    on_set_cursor_wait = QtCore.Signal()
    on_quit_or_hide = QtCore.Signal(str)
    on_magics_applied = QtCore.Signal()
    on_update_available = QtCore.Signal(str)
    on_open_url_and_hide = QtCore.Signal(str)


class MainWindow(BaseWindow):
    """Main (parent) window."""

    tray: SystemTray
    settings_menu: SettingsMenu
    update_checker: UpdateChecker
    com = Communicate()
    capture = Capture()

    def __init__(self, system_info: SystemInfo, args):
        self.settings = init_settings(args)

        super().__init__(
            system_info=system_info,
            screen_idx=0,
            parent=None,
            color=str(self.settings.value("color")),
        )

        self.clipboard = QtWidgets.QApplication.clipboard()

        self.capture.mode = (
            CaptureMode.PARSE
            if self.settings.value("mode") == "parse"
            else CaptureMode.RAW
        )

        self._set_signals()
        self._add_settings_menu()
        self._add_tray()
        self._add_update_checker()
        self._add_notifier()

        self.all_windows: Dict[int, BaseWindow] = {0: self}
        if len(self.system_info.screens) > 1:
            self._init_child_windows()

    def _add_settings_menu(self):
        self.settings_menu = SettingsMenu(self)
        self.settings_menu.com.on_setting_changed.connect(self._update_setting)
        self.settings_menu.com.on_open_url.connect(self.com.on_open_url_and_hide)
        self.settings_menu.com.on_quit_or_hide.connect(
            lambda: self.com.on_quit_or_hide.emit("clicked close in menu")
        )
        self.settings_menu.move(self.width() - self.settings_menu.width() - 20, 20)
        self.settings_menu.show()

    def _add_tray(self):
        self.tray = SystemTray(self)
        self.tray.com.on_capture.connect(self._show_windows)
        self.tray.com.on_exit.connect(lambda: self._quit("clicked exit in tray"))
        if self.settings.value("tray", type=bool):
            self.tray.show()

    def _add_update_checker(self):
        if self.settings.value("update", type=bool):
            checker = UpdateChecker(self, packaged=self.system_info.briefcase_package)
            checker.com.on_version_retrieved.connect(checker.show_update_message)
            checker.com.on_click_get_new_version.connect(self.com.on_open_url_and_hide)
            QtCore.QTimer.singleShot(500, checker.check)

    def _add_notifier(self):
        self.notifier = Notifier(self, self.system_info.platform)
        self.com.on_send_notification.connect(self.notifier.send_notification)
        self.notifier.com.on_notification_sent.connect(
            lambda: self.com.on_quit_or_hide.emit("notification sent")
        )

    def _set_signals(self):
        """Setup signals to trigger program logic."""
        self.com.on_region_selected.connect(self._grab_image)
        self.com.on_image_grabbed.connect(self._prepare_image)
        self.com.on_image_prepared.connect(self._capture_to_ocr)
        self.com.on_ocr_performed.connect(self._apply_magics)
        self.com.on_magics_applied.connect(self._copy_to_clipboard)
        self.com.on_copied_to_clipboard.connect(self._notify_or_close)

        self.com.on_minimize_windows.connect(self._minimize_windows)
        self.com.on_set_cursor_wait.connect(lambda: set_cursor(QtCore.Qt.WaitCursor))
        self.com.on_quit_or_hide.connect(self._quit_or_minimize)
        self.com.on_open_url_and_hide.connect(self._open_url_and_hide)

    ###################
    # UI Manipulation #
    ###################

    def _init_child_windows(self):
        """Initialize child windows with method depending on system."""
        if self.system_info.display_manager != DisplayManager.WAYLAND:
            self._create_all_child_windows()
        elif self.system_info.desktop_environment == DesktopEnvironment.GNOME:
            self.com.on_window_positioned.connect(self._create_next_child_window)
        else:
            logger.error(
                f"NormCap currently doesn't support multi monitor mode"
                f"for {self.system_info.display_manager} "
                f"on {self.system_info.desktop_environment}."
                f"\n{FILE_ISSUE_TEXT}"
            )

    def _create_next_child_window(self):
        """Opening child windows only for next display."""
        if len(self.system_info.screens) > len(self.all_windows):
            index = max(self.all_windows.keys()) + 1
            self._create_child_window(index)

    def _create_all_child_windows(self):
        """Opening all child windows at once."""
        for index in self.system_info.screens:
            if index == self.screen_idx:
                continue
            self._create_child_window(index)

    def _create_child_window(self, index: int):
        """Open a child window for the specified screen."""
        self.all_windows[index] = BaseWindow(
            system_info=self.system_info,
            screen_idx=index,
            parent=self,
            color=str(self.settings.value("color")),
        )
        self.all_windows[index].show()

    def _minimize_windows(self):
        """Hide all windows of normcap."""
        logger.debug("Hiding windows")
        set_cursor(None)
        for window in self.all_windows.values():
            window.hide()

    def _show_windows(self):
        """Make hidden windows visible again."""
        for window in self.all_windows.values():
            if self.system_info.platform == Platform.MACOS:
                if window.macos_border_window:
                    window.macos_border_window.show()
                window.show()
                window.raise_()
                window.activateWindow()
            else:
                window.showFullScreen()

    def _quit_or_minimize(self, reason: str):
        if self.settings.value("tray", type=bool):
            self._minimize_windows()
        else:
            logger.debug("Hiding tray & processing events")
            self.main_window.tray.hide()
            QtWidgets.QApplication.processEvents()
            time.sleep(0.05)
            self._quit(reason)

    @staticmethod
    def _quit(reason: str):
        logger.debug(f"Saved debug images: {tempfile.gettempdir()}{os.sep}normcap")
        logger.info(f"Exit normcap (reason: {reason})")
        QtWidgets.QApplication.quit()

    def _show_or_hide_tray_icon(self):
        if self.settings.value("tray", type=bool):
            logger.debug("Show tray icon")
            self.main_window.tray.show()
        else:
            logger.debug("Hide tray icon")
            self.main_window.tray.hide()

    def _notify_or_close(self):
        if self.settings.value("notification", type=bool):
            self.com.on_send_notification.emit(self.capture)
        else:
            self.com.on_quit_or_hide("detection completed")

    #########################
    # Helper                #
    #########################

    def _open_url_and_hide(self, url):
        """Open url in default browser, then hide to tray or exit."""
        QtGui.QDesktopServices.openUrl(url)
        self.com.on_quit_or_hide.emit("opened web browser")

    def _copy_to_clipboard(self):
        """Copy results to clipboard."""
        # Signal is only temporarily connected to avoid being triggered
        # on arbitrary clipboard changes
        self.clipboard.dataChanged.connect(self.com.on_copied_to_clipboard.emit)
        self.clipboard.dataChanged.connect(self.clipboard.dataChanged.disconnect)

        clipboard_copy = clipboard.init()
        clipboard_copy(self.capture.transformed)
        QtWidgets.QApplication.processEvents()

    #########################
    # Settings              #
    #########################

    def _update_setting(self, data):
        name, value = data
        self.settings.setValue(name, value)

        if name == "tray":
            self._show_or_hide_tray_icon()
        elif name == "mode":
            self.capture.mode = (
                CaptureMode.PARSE if value == "parse" else CaptureMode.RAW
            )

        log_settings(self.settings)

    #####################
    # OCR Functionality #
    #####################

    def _grab_image(self, grab_info: Tuple[Rect, int]):
        """Get image from selected region."""
        logger.info(f"Taking screenshot on {grab_info[0].points}")
        self.capture.rect = grab_info[0]
        self.capture.screen = self.system_info.screens[grab_info[1]]
        self.capture = grab_screen(
            system_info=self.system_info,
            capture=self.capture,
        )
        self.com.on_image_grabbed.emit()

    def _prepare_image(self):
        """Enhance image before performin OCR."""
        if self.capture.image_area > 25:
            logger.debug("Preparing image for OCR")
            self.capture = enhance_image(self.capture)
            self.com.on_image_prepared.emit()
        else:
            logger.warning(f"Area of {self.capture.image_area} too small. Skip OCR")
            self.com.on_quit_or_hide.emit("selection too small")

    def _capture_to_ocr(self):
        """Perform content recognition on grabed image."""
        logger.debug("Performing OCR")
        self.capture = perform_ocr(
            languages=self.settings.value("language"),
            capture=self.capture,
            system_info=self.system_info,
        )
        logger.info(f"Raw text from OCR:\n{self.capture.text}")
        logger.debug(f"Result from OCR:{self.capture}")
        self.com.on_ocr_performed.emit()

    def _apply_magics(self):
        """Beautify/parse content base on magic rules."""
        if self.capture.mode is CaptureMode.PARSE:
            logger.debug("Applying Magics")
            self.capture = apply_magic(self.capture)
            logger.debug(f"Result from applying Magics:{self.capture}")
        if self.capture.mode is CaptureMode.RAW:
            logger.debug("Raw mode. Skip applying Magics and use raw text")
            self.capture.transformed = self.capture.text.strip()
        self.com.on_magics_applied.emit()
