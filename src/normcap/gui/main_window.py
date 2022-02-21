"""Normcap main window."""

import io
import logging
import os
import sys
import tempfile
import time

from PIL import Image
from PySide6 import QtCore, QtGui, QtWidgets

from normcap import ocr
from normcap.gui import system_info, utils
from normcap.gui.base_window import BaseWindow
from normcap.gui.models import Capture, CaptureMode, DesktopEnvironment, Rect, Screen
from normcap.gui.notifier import Notifier
from normcap.gui.settings import init_settings
from normcap.gui.settings_menu import SettingsMenu
from normcap.gui.system_tray import SystemTray
from normcap.gui.update_check import UpdateChecker
from normcap.screengrab import grab_screens

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    """Applications' communication bus."""

    on_region_selected = QtCore.Signal(Rect)
    on_image_cropped = QtCore.Signal()
    on_ocr_performed = QtCore.Signal()
    on_copied_to_clipboard = QtCore.Signal()
    on_send_notification = QtCore.Signal(Capture)
    on_window_positioned = QtCore.Signal()
    on_minimize_windows = QtCore.Signal()
    on_set_cursor_wait = QtCore.Signal()
    on_quit_or_hide = QtCore.Signal(str)
    on_update_available = QtCore.Signal(str)
    on_open_url_and_hide = QtCore.Signal(str)


class MainWindow(BaseWindow):
    """Main (parent) window."""

    tray: SystemTray
    settings_menu: SettingsMenu
    update_checker: UpdateChecker
    com = Communicate()
    capture = Capture()

    def __init__(self, args):
        """Initialize main application window."""
        self.settings = init_settings(
            "normcap",
            "settings",
            initial=args,
            reset=args.get("reset", False),
        )
        self.capture.mode = (
            CaptureMode.PARSE
            if self.settings.value("mode") == "parse"
            else CaptureMode.RAW
        )
        self.screens: dict[int, Screen] = system_info.screens()
        try:
            self._update_screenshots()
        except AssertionError:
            logger.warning("Screenshots not available. Exiting NormCap.")
            sys.exit(1)

        super().__init__(
            screen_idx=0,
            parent=None,
            color=str(self.settings.value("color")),
        )

        self.clipboard = QtWidgets.QApplication.clipboard()

        self._set_signals()
        self._add_tray()
        self._add_settings_menu()
        self._add_update_checker()
        self._add_notifier()

        self.all_windows: dict[int, BaseWindow] = {0: self}
        if len(self.screens) > 1:
            self._init_child_windows()

    def _update_screenshots(self):
        for idx, screenshot in enumerate(grab_screens()):
            utils.save_image_in_tempfolder(screenshot, postfix=f"_raw_screen{idx}")
            self.screens[idx].screenshot = screenshot

    def _add_settings_menu(self):
        self.settings_menu = SettingsMenu(self)
        self.settings_menu.com.on_setting_changed.connect(self._update_setting)
        self.settings_menu.com.on_open_url.connect(self.com.on_open_url_and_hide)
        self.settings_menu.com.on_quit_or_hide.connect(
            lambda: self.com.on_quit_or_hide.emit("clicked close in menu")
        )
        self.settings_menu.move(self.width() - self.settings_menu.width() - 26, 26)
        self.settings_menu.show()

    def _add_tray(self):
        self.tray = SystemTray(self)
        self.tray.com.on_capture.connect(self._show_windows)
        self.tray.com.on_quit.connect(
            lambda: self._quit_application("clicked exit in tray")
        )
        if self.settings.value("tray", type=bool):
            self.tray.show()

    def _add_update_checker(self):
        if self.settings.value("update", type=bool):
            checker = UpdateChecker(self, packaged=system_info.is_briefcase_package())
            checker.com.on_version_retrieved.connect(checker.show_update_message)
            checker.com.on_click_get_new_version.connect(self.com.on_open_url_and_hide)
            QtCore.QTimer.singleShot(500, checker.check)

    def _add_notifier(self):
        self.notifier = Notifier(self)
        self.com.on_send_notification.connect(self.notifier.send_notification)
        self.notifier.com.on_notification_sent.connect(
            lambda: self.com.on_quit_or_hide.emit("notification sent")
        )

    def _set_signals(self):
        """Set up signals to trigger program logic."""
        self.com.on_region_selected.connect(self._crop_image)
        self.com.on_image_cropped.connect(self._capture_to_ocr)
        self.com.on_ocr_performed.connect(self._copy_to_clipboard)
        self.com.on_copied_to_clipboard.connect(self._notify_or_close)

        self.com.on_minimize_windows.connect(self._hide_windows)
        self.com.on_set_cursor_wait.connect(
            lambda: utils.set_cursor(QtCore.Qt.WaitCursor)
        )
        self.com.on_quit_or_hide.connect(self._quit_or_hide)
        self.com.on_open_url_and_hide.connect(self._open_url_and_hide)

    ###################
    # UI Manipulation #
    ###################

    def _init_child_windows(self):
        """Initialize child windows with method depending on system."""
        if not system_info.display_manager_is_wayland():
            self._create_all_child_windows()
        elif system_info.desktop_environment() == DesktopEnvironment.GNOME:
            self.com.on_window_positioned.connect(self._create_next_child_window)

    def _create_next_child_window(self):
        """Open child window only for next display."""
        if len(system_info.screens()) > len(self.all_windows):
            index = max(self.all_windows.keys()) + 1
            self._create_child_window(index)

    def _create_all_child_windows(self):
        """Open all child windows at once."""
        for index in system_info.screens():
            if index == self.screen_idx:
                continue
            self._create_child_window(index)

    def _create_child_window(self, index: int):
        """Open a child window for the specified screen."""
        self.all_windows[index] = BaseWindow(
            screen_idx=index,
            parent=self,
            color=str(self.settings.value("color")),
        )
        self.all_windows[index].show()

    def _hide_windows(self):
        """Hide all windows of normcap."""
        logger.debug("Hide %s window(s)", len(self.all_windows))
        utils.set_cursor(None)
        for window in self.all_windows.values():
            window.hide()

    def _show_windows(self):
        """Make hidden windows visible again."""
        try:
            # Give the menu some time to close before taking screenshot
            time.sleep(0.05)
            self._update_screenshots()
        except AssertionError:
            logger.debug("Abort showing windows.")
            return

        for window in self.all_windows.values():
            window.showFullScreen()

    def _quit_or_hide(self, reason: str):
        if self.settings.value("tray", type=bool):
            self._hide_windows()
        else:
            self._quit_application(reason)

    def _quit_application(self, reason: str):
        self.main_window.tray.hide()
        QtWidgets.QApplication.processEvents()
        time.sleep(0.05)
        logger.debug("Path to debug images: %s%snormcap", tempfile.gettempdir(), os.sep)
        logger.info("Exit normcap (reason: %s)", reason)
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
            self.com.on_quit_or_hide.emit("detection completed")

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Reposition settings menu on resize."""
        if hasattr(self, "settings_menu"):
            self.settings_menu.move(self.width() - self.settings_menu.width() - 26, 26)
        return super().resizeEvent(event)

    #########################
    # Helper                #
    #########################

    def _open_url_and_hide(self, url):
        """Open url in default browser, then hide to tray or exit."""
        logger.debug("Open %s", url)
        QtGui.QDesktopServices.openUrl(url)
        self.com.on_quit_or_hide.emit("opened web browser")

    def _copy_to_clipboard(self):
        """Copy results to clipboard."""
        # Signal is only temporarily connected to avoid being triggered
        # on arbitrary clipboard changes
        self.clipboard.dataChanged.connect(self.com.on_copied_to_clipboard.emit)
        self.clipboard.dataChanged.connect(self.clipboard.dataChanged.disconnect)

        copy = utils.copy_to_clipboard()
        copy(self.capture.ocr_text)
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

        logger.debug(
            "Settings:\n%s",
            [(k, self.settings.value(k)) for k in self.settings.allKeys()],
        )

    #####################
    # OCR Functionality #
    #####################

    def _crop_image(self, grab_info: tuple[Rect, int]):
        """Crop image to selected region."""
        logger.info("Crop image to selected region %s", grab_info[0].points)
        rect, screen_idx = grab_info

        screenshot = self.screens[screen_idx].screenshot
        if not screenshot:
            raise TypeError("Screenshot is None!")

        self.capture.rect = rect
        self.capture.screen = self.screens[screen_idx]
        self.capture.image = screenshot.copy(QtCore.QRect(*rect.geometry))

        utils.save_image_in_tempfolder(self.capture.image, postfix="_cropped")

        self.com.on_image_cropped.emit()

    @staticmethod
    def _qimage_to_pil_image(image: QtGui.QImage):
        """Cast QImage to pillow Image type."""
        ba = QtCore.QByteArray()
        buffer = QtCore.QBuffer(ba)
        buffer.open(QtCore.QIODevice.ReadWrite)
        image.save(buffer, "PNG")  # type:ignore
        return Image.open(io.BytesIO(buffer.data()))

    def _capture_to_ocr(self):
        """Perform content recognition on grabed image."""
        if self.capture.image_area < 25:
            logger.warning("Area of %s too small. Skip OCR", self.capture.image_area)
            self.com.on_quit_or_hide.emit("selection too small")
            return

        logger.debug("Start OCR")
        ocr_result = ocr.recognize(
            languages=self.settings.value("language"),
            image=self._qimage_to_pil_image(self.capture.image),
            tessdata_path=system_info.get_tessdata_path(),
            parse=self.capture.mode is CaptureMode.PARSE,
            resize_factor=3.2,
            padding_size=80,
        )
        utils.save_image_in_tempfolder(ocr_result.image, postfix="_enhanced")

        self.capture.ocr_text = ocr_result.text
        self.capture.ocr_applied_magic = ocr_result.best_scored_magic

        logger.info("Text from OCR:\n%s", self.capture.ocr_text)
        self.com.on_ocr_performed.emit()
