"""Create system tray and its menu."""
import io
import logging
import os
import tempfile
import time
from functools import partial

from PIL import Image
from PySide6 import QtCore, QtGui, QtWidgets

from normcap import __version__, ocr
from normcap.gui import system_info, utils
from normcap.gui.models import Capture, CaptureMode, DesktopEnvironment, Rect, Screen
from normcap.gui.notifier import Notifier
from normcap.gui.settings import Settings
from normcap.gui.update_check import UpdateChecker
from normcap.gui.window import Window
from normcap.screengrab import grab_screens

logger = logging.getLogger(__name__)

# TODO: Remove pylint disable no-member when https://github.com/PyCQA/pylint/issues/5378


class Communicate(QtCore.QObject):
    """TrayMenus' communication bus."""

    on_tray_menu_capture = QtCore.Signal()
    on_quit = QtCore.Signal()
    on_ocr_performed = QtCore.Signal()
    on_copied_to_clipboard = QtCore.Signal()
    on_send_notification = QtCore.Signal(Capture)
    on_window_positioned = QtCore.Signal()
    on_open_url_and_hide = QtCore.Signal(str)
    on_set_cursor_wait = QtCore.Signal()
    on_close_or_exit = QtCore.Signal(str)
    on_region_selected = QtCore.Signal(Rect)
    on_image_cropped = QtCore.Signal()
    on_minimize_windows = QtCore.Signal()
    on_screenshots_updated = QtCore.Signal()


class SystemTray(QtWidgets.QSystemTrayIcon):
    """System tray icon with menu."""

    capture = Capture()
    windows: dict[int, Window] = {}

    def __init__(self, parent, args):
        logger.debug("Set up tray icon")
        super().__init__(parent)

        self.com = Communicate()
        self.settings = Settings("normcap", "settings", init_settings=args)
        if args.get("reset", False):
            self.settings.reset()

        self.capture.mode = (
            CaptureMode.PARSE
            if self.settings.value("mode") == "parse"
            else CaptureMode.RAW
        )
        self.clipboard = QtWidgets.QApplication.clipboard()
        self.screens: dict[int, Screen] = system_info.screens()

        self.setIcon(utils.get_icon("tray.png", "tool-magic-symbolic"))
        self._add_tray_menu()
        self._add_update_checker()
        self._add_notifier()
        self._set_signals()
        self._update_screenshots()

    def _set_signals(self):
        """Set up signals to trigger program logic."""
        self.com.on_tray_menu_capture.connect(self._delayed_update_screenshots)
        self.com.on_screenshots_updated.connect(self._show_windows)
        self.com.on_quit.connect(lambda: self._exit_application("clicked exit in tray"))
        self.com.on_region_selected.connect(self._close_windows)
        self.com.on_region_selected.connect(self._crop_image)
        self.com.on_image_cropped.connect(self._capture_to_ocr)
        self.com.on_ocr_performed.connect(self._copy_to_clipboard)
        self.com.on_copied_to_clipboard.connect(self._notify_or_close)

        self.com.on_minimize_windows.connect(self._close_windows)
        self.com.on_set_cursor_wait.connect(
            lambda: utils.set_cursor(QtCore.Qt.WaitCursor)
        )
        self.com.on_close_or_exit.connect(self._close_or_exit)
        self.com.on_open_url_and_hide.connect(self._open_url_and_hide)

    def _add_update_checker(self):
        if self.settings.value("update", type=bool):
            checker = UpdateChecker(self, packaged=system_info.is_prebuild_package())
            checker.com.on_version_retrieved.connect(checker.show_update_message)
            checker.com.on_click_get_new_version.connect(self.com.on_open_url_and_hide)
            QtCore.QTimer.singleShot(500, checker.check)

    def _add_notifier(self):
        self.notifier = Notifier(self)
        self.com.on_send_notification.connect(self.notifier.send_notification)
        self.notifier.com.on_notification_sent.connect(
            lambda: self.com.on_close_or_exit.emit("notification sent")
        )

    def _update_screenshots(self):
        """Get new screenshots and cache them."""
        screens = grab_screens()

        if not screens:
            logger.error("Could not grab screenshots.")
            return

        for idx, screenshot in enumerate(screens):
            utils.save_image_in_tempfolder(screenshot, postfix=f"_raw_screen{idx}")
            self.screens[idx].screenshot = screenshot

        self.com.on_screenshots_updated.emit()

    def _delayed_update_screenshots(self):
        """Wait before updating screenshot to allow tray menu to hide.

        Avoids having the tray menu itself on the screenshot.
        """
        time.sleep(0.15)
        self._update_screenshots()

    def _add_tray_menu(self):
        """Create menu for system tray."""
        menu = QtWidgets.QMenu()

        action = QtGui.QAction("Capture", menu)
        action.triggered.connect(  # pylint: disable=no-member
            self.com.on_tray_menu_capture.emit
        )
        menu.addAction(action)

        action = QtGui.QAction("Exit", menu)
        action.triggered.connect(self.com.on_quit.emit)  # pylint: disable=no-member
        menu.addAction(action)

        self.setContextMenu(menu)

    def _show_windows(self):
        """Initialize child windows with method depending on system."""
        if not system_info.display_manager_is_wayland():
            for index in system_info.screens():
                self._create_window(index)

        elif system_info.desktop_environment() in [
            DesktopEnvironment.GNOME,
            DesktopEnvironment.KDE,
        ]:
            self._create_next_window()

    def _create_next_window(self):
        """Open child window only for next display."""
        if len(system_info.screens()) > len(self.windows):
            index = len(self.windows.keys())
            self._create_window(index)

    def _create_window(self, index: int):
        """Open a child window for the specified screen."""
        new_window = Window(
            screen_idx=index,
            parent=self,
            color=str(self.settings.value("color")),
        )
        if index == 0:
            new_window.add_settings_menu(self)

        new_window.set_fullscreen()
        self.windows[index] = new_window

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

        self.capture.mode = CaptureMode[self.settings.value("mode").upper()]
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
            self.com.on_close_or_exit.emit("selection too small")
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

    #########################
    # Helper                #
    #########################

    def _open_url_and_hide(self, url):
        """Open url in default browser, then hide to tray or exit."""
        logger.debug("Open %s", url)
        QtGui.QDesktopServices.openUrl(url)
        self.com.on_close_or_exit.emit("opened web browser")

    def _copy_to_clipboard(self):
        """Copy results to clipboard."""
        # Signal is only temporarily connected to avoid being triggered
        # on arbitrary clipboard changes
        self.clipboard.dataChanged.connect(self.com.on_copied_to_clipboard.emit)
        self.clipboard.dataChanged.connect(self.clipboard.dataChanged.disconnect)

        copy = utils.copy_to_clipboard()
        copy(self.capture.ocr_text)
        QtWidgets.QApplication.processEvents()

    def _notify_or_close(self):
        if self.settings.value("notification", type=bool):
            self.com.on_send_notification.emit(self.capture)
        else:
            self.com.on_close_or_exit.emit("detection completed")

    def _close_windows(self):
        """Hide all windows of normcap."""
        logger.debug("Hide %s window(s)", len(self.windows))
        utils.set_cursor(None)
        for window in self.windows.values():
            window.close()
        self.windows = {}

    def _close_or_exit(self, reason: str):
        if self.settings.value("tray", type=bool):
            self._close_windows()
        elif reason == "notification sent":
            # Hide but delay exit to give notification enough time to show up.
            self._close_windows()
            delayed_exit = partial(
                self._exit_application, reason="notification sent delaying exit"
            )
            QtCore.QTimer.singleShot(5000, delayed_exit)
        else:
            self._exit_application(reason)

    def _exit_application(self, reason: str):
        self.hide()
        QtWidgets.QApplication.processEvents()
        time.sleep(0.05)
        logger.debug("Path to debug images: %s%snormcap", tempfile.gettempdir(), os.sep)
        logger.info("Exit normcap (reason: %s)", reason)
        QtWidgets.QApplication.quit()
