"""Normcap main window."""

import os
import sys
import tempfile
import textwrap
import time
from typing import Dict, Tuple

import importlib_resources
from PySide2 import QtCore, QtGui, QtWidgets

import normcap.clipboard as clipboard
from normcap import __version__
from normcap.enhance import enhance_image
from normcap.logger import logger
from normcap.magic import apply_magic
from normcap.models import (
    FILE_ISSUE_TEXT,
    Capture,
    CaptureMode,
    Config,
    DesktopEnvironment,
    DisplayManager,
    Platform,
    Rect,
    SystemInfo,
)
from normcap.ocr import perform_ocr
from normcap.screengrab import grab_screen
from normcap.window_base import WindowBase


class Communicate(QtCore.QObject):
    """Applications' communication bus."""

    onRegionSelected = QtCore.Signal(Rect)
    onImageGrabbed = QtCore.Signal()
    onOcrPerformed = QtCore.Signal()
    onImagePrepared = QtCore.Signal()
    onCopiedToClipboard = QtCore.Signal()
    onWindowPositioned = QtCore.Signal()
    onMinimizeWindows = QtCore.Signal()
    onSetCursorWait = QtCore.Signal()
    onQuitOrHide = QtCore.Signal()
    onMagicsApplied = QtCore.Signal()


class WindowMain(WindowBase):
    """Main (parent) window."""

    tray: QtWidgets.QSystemTrayIcon

    def __init__(
        self,
        config: Config,
        system_info: SystemInfo,
    ):
        super().__init__(
            system_info=system_info, screen_idx=0, parent=None, color=config.color
        )
        self.config: Config = config

        self.capture: Capture = Capture()
        self.com = Communicate()

        self.tray_icon = self.get_icon("tray.png")

        if self.system_info.platform == Platform.WINDOWS:
            self.notification_icon = self.get_icon("normcap.png")
        else:
            self.notification_icon = self.tray_icon

        self.all_windows: Dict[int, WindowBase] = {0: self}
        self.multi_monitor_mode = len(self.system_info.screens) > 1

        self.set_signals()
        self.set_system_tray()

        if self.multi_monitor_mode:
            self.init_child_windows()

    def set_signals(self):
        """Setup signals to trigger program logic."""
        self.com.onRegionSelected.connect(self.grab_image)
        self.com.onImageGrabbed.connect(self.prepare_image)
        self.com.onImagePrepared.connect(self.capture_to_ocr)
        self.com.onOcrPerformed.connect(self.apply_magics)
        self.com.onMagicsApplied.connect(self.copy_to_clipboard)
        self.com.onCopiedToClipboard.connect(self.send_notification)
        self.com.onCopiedToClipboard.connect(self.restore_cursor)

        self.com.onMinimizeWindows.connect(self.minimize_windows)
        self.com.onSetCursorWait.connect(self.set_cursor_wait)
        self.com.onQuitOrHide.connect(self.quit_or_minimize)

    ###################
    # UI Manipulation #
    ###################

    @staticmethod
    def get_icon(icon_file: str):
        """Load icon from system or if not available from resources."""
        icon = QtGui.QIcon.fromTheme("tool-magic-symbolic")
        if not icon:
            with importlib_resources.path("normcap.resources", icon_file) as fp:
                icon_path = str(fp.absolute())
            icon = QtGui.QIcon()
            icon.addFile(icon_path)
        return icon

    @staticmethod
    def set_cursor_wait():
        """Show in-progress cursor for application."""
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        QtWidgets.QApplication.processEvents()

    @staticmethod
    def restore_cursor():
        """Restore normal cursor."""
        QtWidgets.QApplication.restoreOverrideCursor()
        QtWidgets.QApplication.processEvents()

    def init_child_windows(self):
        """Initialize child windows with method depending on system."""
        if self.system_info.display_manager != DisplayManager.WAYLAND:
            self.create_all_child_windows()
        else:
            if self.system_info.desktop_environment == DesktopEnvironment.GNOME:
                self.com.onWindowPositioned.connect(self.create_next_child_window)
            else:
                logger.error(
                    f"NormCap currently doesn't support multi monitor mode"
                    f"for {self.system_info.display_manager} "
                    f"on {self.system_info.desktop_environment}."
                    f"\n{FILE_ISSUE_TEXT}"
                )

    def create_next_child_window(self):
        """Instantiate child windows in multi screen setting."""
        if len(self.system_info.screens) > len(self.all_windows):
            index = max(self.all_windows.keys()) + 1
            self.create_child_window(index)

    def create_all_child_windows(self):
        """Opening all child windows at once."""
        for index in self.system_info.screens:
            if index == self.screen_idx:
                continue
            self.create_child_window(index)

    def create_child_window(self, index: int):
        """Open a child window for the specified screen."""
        self.all_windows[index] = WindowBase(
            system_info=self.system_info,
            screen_idx=index,
            parent=self,
            color=self.config.color,
        )
        self.all_windows[index].show()

    def minimize_windows(self):
        """Hide all windows of normcap."""
        self.restore_cursor()
        for window in self.all_windows.values():
            window.hide()

    def show_windows(self):
        """Make hidden windows visible again."""
        for window in self.all_windows.values():
            if self.system_info.platform == Platform.MACOS:
                window.show()
                window.raise_()
                window.activateWindow()
            else:
                window.showFullScreen()

    def quit_or_minimize(self):
        """Minimize application if in tray-mode, else exit."""
        # Necessary to get text to clipboard before exitting
        if self.config.tray:
            logger.debug("Hiding windows to tray")
            self.minimize_windows()
        else:
            logger.debug("Hiding tray & processing events")
            self.main_window.tray.hide()
            QtWidgets.QApplication.processEvents()
            time.sleep(0.05)
            logger.debug(
                "Images have been saved for debugging in: "
                + f"{tempfile.gettempdir()}{os.sep}normcap"
            )
            logger.debug("Exit normcap.")
            QtWidgets.QApplication.quit()

    #########################
    # Tray and Notification #
    #########################

    def set_system_tray(self):
        """Setting up tray icon."""
        logger.debug("Setting up tray icon")
        menu = self.create_tray_menu()
        self.main_window.tray = QtWidgets.QSystemTrayIcon()
        self.main_window.tray.setIcon(self.tray_icon)
        self.main_window.tray.setContextMenu(menu)
        if self.config.tray:
            logger.debug("Show tray icon")
            self.main_window.tray.show()

    def create_tray_menu(self):
        """Create menu for system tray."""
        menu = QtWidgets.QMenu()

        capture_action = menu.addAction("Capture")
        capture_action.triggered.connect(self.show_windows)
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(sys.exit)

        menu.addSeparator()

        website_action = menu.addAction(f"NormCap {__version__} Website")
        website_action.triggered.connect(
            lambda: QtGui.QDesktopServices.openUrl("https://github.com/dynobo/normcap")
        )
        update_action = menu.addAction("- Releases")
        update_action.triggered.connect(
            lambda: QtGui.QDesktopServices.openUrl(
                "https://github.com/dynobo/normcap/releases"
            )
        )
        faq_action = menu.addAction("- FAQ")
        faq_action.triggered.connect(
            lambda: QtGui.QDesktopServices.openUrl(
                "https://github.com/dynobo/normcap/blob/main/FAQ.md"
            )
        )
        issue_action = menu.addAction("- Report Problem")
        issue_action.triggered.connect(
            lambda: QtGui.QDesktopServices.openUrl(
                "https://github.com/dynobo/normcap/issues"
            )
        )
        return menu

    def send_notification(self):
        """Setting up tray icon."""
        title, message = self.compose_notification()
        self.main_window.tray.show()
        self.main_window.tray.showMessage(title, message, self.notification_icon)

        # Delay quit or hide to get notification enough time to show up.
        delay = 5000 if self.system_info.platform == Platform.WINDOWS else 500
        QtCore.QTimer.singleShot(delay, self.com.onQuitOrHide.emit)

    def compose_notification(self) -> Tuple[str, str]:
        """Extract message text out of captures object and include icon."""
        # Message text
        text = self.capture.transformed.replace(os.linesep, " ")
        text = textwrap.shorten(text, width=45)
        if len(text) < 1:
            text = "Please try again."

        # Message title
        title = ""
        count = 0
        if len(self.capture.transformed) < 1:
            title += "Nothing!"
        elif self.capture.best_magic == "ParagraphMagic":
            count = self.capture.transformed.count(os.linesep * 2) + 1
            title += f"{count} paragraph"
        elif self.capture.best_magic == "EmailMagic":
            count = self.capture.transformed.count("@")
            title += f"{count} email"
        elif self.capture.best_magic == "SingleLineMagic":
            count = self.capture.transformed.count(" ") + 1
            title += f"{count} word"
        elif self.capture.best_magic == "MultiLineMagic":
            count = self.capture.transformed.count("\n") + 1
            title += f"{count} line"
        elif self.capture.best_magic == "UrlMagic":
            count = self.capture.transformed.count("http")
            title += f"{count} URL"
        elif self.capture.mode == CaptureMode.RAW:
            count = len(self.capture.transformed)
            title += f"{count} char"
        title += f"{'s' if count > 1 else ''} captured"

        return title, text

    #####################
    # OCR Functionality #
    #####################

    def grab_image(self, grab_info: Tuple[Rect, int]):
        """Get image from selected region."""
        logger.debug(f"Taking screenshot on {grab_info[0].points}")
        self.capture.rect = grab_info[0]
        self.capture.screen = self.system_info.screens[grab_info[1]]
        self.capture = grab_screen(
            system_info=self.system_info,
            capture=self.capture,
        )
        self.com.onImageGrabbed.emit()

    def prepare_image(self):
        """Enhance image before performin OCR."""
        if self.capture.image_area > 25:
            logger.debug("Preparing image for OCR")
            self.capture = enhance_image(self.capture)
            self.com.onImagePrepared.emit()
        else:
            logger.warning(f"Area of {self.capture.image_area} too small. Skip OCR.")
            self.com.onQuitOrHide.emit()

    def capture_to_ocr(self):
        """Perform content recognition on grabed image."""

        logger.debug("Performing OCR")
        self.capture = perform_ocr(
            language=self.config.language,
            capture=self.capture,
            system_info=self.system_info,
        )
        logger.info(f"Raw text from OCR:\n{self.capture.text}")
        logger.debug(f"Result from OCR:{self.capture}")
        self.com.onOcrPerformed.emit()

    def apply_magics(self):
        """Beautify/parse content base on magic rules."""
        if self.capture.mode is CaptureMode.PARSE:
            logger.debug("Applying Magics")
            self.capture = apply_magic(self.capture)
            logger.debug(f"Result from applying Magics:{self.capture}")
        if self.capture.mode is CaptureMode.RAW:
            logger.debug("Raw mode. Skip applying Magics and use raw text.")
            self.capture.transformed = self.capture.text.strip()
        self.com.onMagicsApplied.emit()

    def copy_to_clipboard(self):
        """Copy results to clipboard."""
        logger.info(
            f"Copying (transformed) text to clipboard:\n{self.capture.transformed}"
        )
        clipboard_copy = clipboard.init()
        clipboard_copy(self.capture.transformed)

        QtWidgets.QApplication.processEvents()
        time.sleep(1.05)
        self.com.onCopiedToClipboard.emit()
