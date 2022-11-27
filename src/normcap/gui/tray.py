"""Create system tray and its menu."""
import datetime
import io
import logging
import os
import sys
import tempfile
import time
from functools import partial
from typing import Any, Iterable, NoReturn

from normcap import __version__, clipboard, ocr, screengrab
from normcap.gui import system_info, utils
from normcap.gui.constants import UPDATE_CHECK_INTERVAL_DAYS
from normcap.gui.models import Capture, CaptureMode, DesktopEnvironment, Rect, Screen
from normcap.gui.notifier import Notifier
from normcap.gui.settings import Settings
from normcap.gui.update_check import UpdateChecker
from normcap.gui.window import Window
from normcap.version import Version
from PIL import Image
from PySide6 import QtCore, QtGui, QtWidgets

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    """TrayMenus' communication bus."""

    on_tray_menu_capture_clicked = QtCore.Signal()
    on_quit = QtCore.Signal()
    on_ocr_performed = QtCore.Signal()
    on_copied_to_clipboard = QtCore.Signal()
    on_send_notification = QtCore.Signal(Capture)
    on_window_positioned = QtCore.Signal()
    on_open_url_and_hide = QtCore.Signal(str)
    on_close_or_exit = QtCore.Signal(str)
    on_region_selected = QtCore.Signal(Rect)
    on_image_cropped = QtCore.Signal()
    on_screenshots_updated = QtCore.Signal()


class SystemTray(QtWidgets.QSystemTrayIcon):
    """System tray icon with menu."""

    capture = Capture()
    windows: dict[int, Window] = {}

    def __init__(self, parent: QtCore.QObject, args: dict[str, Any]) -> None:
        logger.debug("System info:\n%s", system_info.to_dict())
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
        self.copy_to_clipboard = clipboard.get_copy_func()

        self.screens: list[Screen] = system_info.screens()

        self._set_tray_icon()
        self._add_tray_menu()
        self._ensure_screenshot_permission()
        self._add_update_checker()
        self._add_notifier()
        self._set_signals()
        self._update_screenshots(delayed=False)

    def _ensure_screenshot_permission(self) -> None:
        if screengrab.has_screenshot_permission():
            return

        if sys.platform == "darwin":
            # Reset privacy permission in case of new NormCap version. This is necessary
            # because somehow the setting is associated with the binary and won't work
            # after it got updated.
            if self.settings.value("version") != __version__:
                self.settings.setValue("version", __version__)
                screengrab.macos_reset_screenshot_permission()

            # Trigger permission request to make the NormCap entry available in settings
            screengrab.macos_request_screenshot_permission()

            # Message box to explain what's happening and open the preferences
            app = "NormCap" if system_info.get_prebuild_package_type() else "Terminal"
            button = QtWidgets.QMessageBox.critical(
                None,
                "Error!",
                f"{app} is missing permissions for 'Screen Recording'.\n\n"
                + "Grant the permissions via 'Privacy & Security' settings "
                + "and restart NormCap.\n\nClick OK to exit.",
                buttons=QtWidgets.QMessageBox.Open | QtWidgets.QMessageBox.Cancel,
            )
            if button == QtWidgets.QMessageBox.Open:
                logger.debug("Open macOS privacy settings")
                screengrab.macos_open_privacy_settings()

            self._exit_application("Screen Recording permissions missing on macOS")

    def _set_tray_icon(self) -> None:
        self.setIcon(utils.get_icon("tray.png", "tool-magic-symbolic"))

    def _color_tray_icon(self) -> None:
        if sizes := self.icon().availableSizes():
            pixmap = self.icon().pixmap(sizes[-1])
            mask = pixmap.createMaskFromColor(
                QtGui.QColor("transparent"), QtCore.Qt.MaskMode.MaskInColor
            )
            pixmap.fill(QtGui.QColor(str(self.settings.value("color"))))
            pixmap.setMask(mask)
            self.setIcon(QtGui.QIcon(pixmap))

            QtCore.QTimer.singleShot(5000, self._set_tray_icon)

    def _set_signals(self) -> None:
        """Set up signals to trigger program logic."""
        self.activated.connect(self._handle_tray_click)
        self.com.on_tray_menu_capture_clicked.connect(self._update_screenshots)
        self.com.on_screenshots_updated.connect(self._show_windows)
        self.com.on_quit.connect(lambda: self._exit_application("clicked exit in tray"))
        self.com.on_region_selected.connect(self._close_windows)
        self.com.on_region_selected.connect(self._crop_image)
        self.com.on_image_cropped.connect(self._capture_to_ocr)
        self.com.on_ocr_performed.connect(self._copy_to_clipboard)
        self.com.on_copied_to_clipboard.connect(self._notify_or_close)
        self.com.on_copied_to_clipboard.connect(self._color_tray_icon)
        self.com.on_close_or_exit.connect(self._close_or_exit)
        self.com.on_open_url_and_hide.connect(self._open_url_and_hide)

    def _handle_tray_click(
        self, reason: QtWidgets.QSystemTrayIcon.ActivationReason
    ) -> None:
        logger.debug("Tray event: %s", reason)
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.Trigger:
            self._update_screenshots()

    def _add_update_checker(self) -> None:
        if self.settings.value("update", type=bool) is False:
            return

        interval = datetime.timedelta(days=UPDATE_CHECK_INTERVAL_DAYS)
        today_minus_interval = f"{datetime.datetime.now() - interval:%Y-%m-%d}"
        if (
            str(self.settings.value("last-update-check", type=str))
            > today_minus_interval
        ):
            return

        checker = UpdateChecker(
            self, packaged=system_info.get_prebuild_package_type() is not None
        )
        checker.com.on_version_parsed.connect(self._update_time_of_last_update_check)
        checker.com.on_click_get_new_version.connect(self.com.on_open_url_and_hide)
        QtCore.QTimer.singleShot(500, checker.check)

    def _update_time_of_last_update_check(self, newest_version: Version) -> None:
        if newest_version is not None:
            today = f"{datetime.datetime.now():%Y-%m-%d}"
            self.settings.setValue("last-update-check", today)

    def _add_notifier(self) -> None:
        self.notifier = Notifier(self)
        self.com.on_send_notification.connect(self.notifier.send_notification)
        self.notifier.com.on_notification_sent.connect(
            lambda: self.com.on_close_or_exit.emit("notification sent")
        )

    def _update_screenshots(self, delayed: bool = True) -> None:
        """Get new screenshots and cache them."""
        if delayed:
            time.sleep(0.15)

        capture = screengrab.get_capture_func()
        screens = capture()

        if not screens:
            logger.error("Could not grab screenshot.")
            return

        for idx, screenshot in enumerate(screens):
            utils.save_image_in_tempfolder(screenshot, postfix=f"_raw_screen{idx}")
            self.screens[idx].screenshot = screenshot

        self.com.on_screenshots_updated.emit()

    def _add_tray_menu(self) -> None:
        """Create menu for system tray."""
        menu = QtWidgets.QMenu()

        action = QtGui.QAction("Capture", menu)
        action.triggered.connect(self.com.on_tray_menu_capture_clicked.emit)
        menu.addAction(action)

        action = QtGui.QAction("Exit", menu)
        action.triggered.connect(self.com.on_quit.emit)
        menu.addAction(action)

        self.setContextMenu(menu)

    def _show_windows(self) -> None:
        """Initialize child windows with method depending on system."""
        if not system_info.display_manager_is_wayland():
            for index in range(len(system_info.screens())):
                self._create_window(index)

        elif system_info.desktop_environment() in [
            DesktopEnvironment.GNOME,
            DesktopEnvironment.KDE,
        ]:
            self.com.on_window_positioned.connect(self._create_next_window)
            self._create_next_window()

    def _create_next_window(self) -> None:
        """Open child window only for next display."""
        if len(system_info.screens()) > len(self.windows):
            index = len(self.windows.keys())
            self._create_window(index)

    def _create_window(self, index: int) -> None:
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

    def _crop_image(self, grab_info: tuple[Rect, int]) -> None:
        """Crop image to selected region."""
        logger.info("Crop image to selected region %s", grab_info[0].points)
        rect, screen_idx = grab_info

        screenshot = self.screens[screen_idx].screenshot
        if not screenshot:
            raise TypeError("Screenshot is None!")

        self.capture.mode = CaptureMode[str(self.settings.value("mode")).upper()]
        self.capture.rect = rect
        self.capture.screen = self.screens[screen_idx]
        self.capture.image = screenshot.copy(QtCore.QRect(*rect.geometry))

        utils.save_image_in_tempfolder(self.capture.image, postfix="_cropped")

        self.com.on_image_cropped.emit()

    @staticmethod
    def _qimage_to_pil_image(image: QtGui.QImage) -> Image.Image:
        """Cast QImage to pillow Image type."""
        ba = QtCore.QByteArray()
        buffer = QtCore.QBuffer(ba)
        buffer.open(QtCore.QIODevice.ReadWrite)
        image.save(buffer, "PNG")  # type:ignore
        return Image.open(io.BytesIO(buffer.data()))

    def _capture_to_ocr(self) -> None:
        """Perform content recognition on grabed image."""
        if self.capture.image_area < 25:
            logger.warning("Area of %s too small. Skip OCR", self.capture.image_area)
            self.com.on_close_or_exit.emit("selection too small")
            return

        logger.debug("Start OCR")
        language = self.settings.value("language")
        if not isinstance(language, str) and not isinstance(language, Iterable):
            raise TypeError()
        ocr_result = ocr.recognize(
            languages=language,
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

    def _open_url_and_hide(self, url: str) -> None:
        """Open url in default browser, then hide to tray or exit."""
        logger.debug("Open %s", url)
        QtGui.QDesktopServices.openUrl(url)
        self.com.on_close_or_exit.emit("opened web browser")

    def _copy_to_clipboard(self) -> None:
        """Copy results to clipboard."""
        # Signal is only temporarily connected to avoid being triggered
        # on arbitrary clipboard changes

        self.copy_to_clipboard(self.capture.ocr_text)
        self.com.on_copied_to_clipboard.emit()

    def _notify_or_close(self) -> None:
        if self.settings.value("notification", type=bool):
            self.com.on_send_notification.emit(self.capture)
        else:
            self.com.on_close_or_exit.emit("detection completed")

    def _close_windows(self) -> None:
        """Hide all windows of normcap."""
        logger.debug("Hide %s window(s)", len(self.windows))
        utils.set_cursor(None)
        for window in self.windows.values():
            window.close()
        self.windows = {}

    def _close_or_exit(self, reason: str) -> None:
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

    def _exit_application(self, reason: str) -> NoReturn:
        self.hide()
        QtWidgets.QApplication.processEvents()
        time.sleep(0.05)
        logger.debug("Path to debug images: %s%snormcap", tempfile.gettempdir(), os.sep)
        logger.info("Exit normcap (reason: %s)", reason)
        # The preferable QApplication.quit() doesn't work reliably on macOS. E.g. when
        # right clicking on "close" in tray menu, NormCap process keeps running.
        sys.exit(0)
