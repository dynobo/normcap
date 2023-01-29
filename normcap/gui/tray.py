"""Create system tray and its menu."""
import datetime
import io
import logging
import os
import sys
import tempfile
import time
from functools import partial
from pathlib import Path
from typing import Any, Iterable, NoReturn

from PIL import Image
from PySide6 import QtCore, QtGui, QtWidgets

from normcap import __version__, clipboard, ocr, screengrab
from normcap.gui import resources, system_info
from normcap.gui.language_manager import LanguageManager
from normcap.gui.menu_button import MenuButton
from normcap.gui.models import Capture, CaptureMode, DesktopEnvironment, Rect, Screen
from normcap.gui.notifier import Notifier
from normcap.gui.settings import Settings
from normcap.gui.update_check import UpdateChecker
from normcap.gui.window import Window

if not resources.qt_resource_data:
    raise ValueError("Couldn't load QT resources")

logger = logging.getLogger(__name__)

UPDATE_CHECK_INTERVAL_DAYS = 7


def _save_image_in_tempfolder(
    image: Image.Image, postfix: str = "", log_level: int = logging.DEBUG
) -> None:
    """For debugging it can be useful to store the cropped image."""
    if logger.getEffectiveLevel() == log_level:
        file_dir = Path(tempfile.gettempdir()) / "normcap"
        file_dir.mkdir(exist_ok=True)
        now = datetime.datetime.now()
        file_name = f"{now:%Y-%m-%d_%H-%M-%S_%f}{postfix}.png"
        logger.debug("Save debug image as %s", file_dir / file_name)
        image.save(str(file_dir / file_name))


class Communicate(QtCore.QObject):
    """TrayMenus' communication bus."""

    on_close_or_exit = QtCore.Signal(str)
    on_copied_to_clipboard = QtCore.Signal()
    on_image_cropped = QtCore.Signal()
    on_manage_languages = QtCore.Signal()
    on_ocr_performed = QtCore.Signal()
    on_open_url_and_hide = QtCore.Signal(str)
    on_quit = QtCore.Signal()
    on_region_selected = QtCore.Signal(Rect)
    on_screenshots_updated = QtCore.Signal()
    on_send_notification = QtCore.Signal(Capture)
    on_tray_menu_capture_clicked = QtCore.Signal()
    on_window_positioned = QtCore.Signal()


class SystemTray(QtWidgets.QSystemTrayIcon):
    """System tray icon with menu."""

    capture = Capture()
    windows: dict[int, Window] = {}

    def __init__(self, parent: QtCore.QObject, args: dict[str, Any]) -> None:
        logger.debug("System info:\n%s", system_info.to_dict())
        super().__init__(parent)

        self.com = Communicate()

        self.settings = Settings("normcap", "settings", init_settings=args)
        self._sanatize_active_language(self.settings)

        if args.get("reset", False):
            self.settings.reset()

        self.capture.mode = (
            CaptureMode.PARSE
            if self.settings.value("mode") == "parse"
            else CaptureMode.RAW
        )

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
            app = "NormCap" if system_info.is_prebuild_package() else "Terminal"
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
        self.setIcon(QtGui.QIcon.fromTheme("tool-magic-symbolic", QtGui.QIcon(":tray")))

    @QtCore.Slot()
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
        self.com.on_manage_languages.connect(self._open_language_manager)

    @QtCore.Slot(QtWidgets.QSystemTrayIcon.ActivationReason)
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
        today_sub_interval = f"{datetime.datetime.now() - interval:%Y-%m-%d}"
        if str(self.settings.value("last-update-check", type=str)) > today_sub_interval:
            return

        checker = UpdateChecker(self, packaged=system_info.is_prebuild_package())
        checker.com.on_version_checked.connect(self._update_time_of_last_update_check)
        checker.com.on_click_get_new_version.connect(self.com.on_open_url_and_hide)
        QtCore.QTimer.singleShot(500, checker.check)

    def _update_time_of_last_update_check(self, newest_version: str) -> None:
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
            _save_image_in_tempfolder(screenshot, postfix=f"_raw_screen{idx}")
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

    @QtCore.Slot()
    def _show_windows(self) -> None:
        """Initialize child windows with method depending on system."""
        if not system_info.display_manager_is_wayland():
            for index in range(len(system_info.screens())):
                self._create_window(index)

        elif system_info.desktop_environment() in (
            DesktopEnvironment.GNOME,
            DesktopEnvironment.KDE,
        ):
            self.com.on_window_positioned.connect(self._create_next_window)
            self._create_next_window()

    def _create_next_window(self) -> None:
        """Open child window only for next display."""
        if len(system_info.screens()) > len(self.windows):
            index = len(self.windows.keys())
            self._create_window(index)

    def _create_window(self, index: int) -> None:
        """Open a child window for the specified screen."""
        new_window = Window(screen=self.screens[index], settings=self.settings)
        new_window.com.on_esc_key_pressed.connect(
            lambda: self.com.on_close_or_exit.emit("esc button pressed")
        )
        new_window.com.on_region_selected.connect(self.com.on_region_selected)
        new_window.com.on_window_positioned.connect(self.com.on_window_positioned)
        if index == 0:
            new_window.ui_layer.setLayout(self._create_menu_button())

        new_window.set_fullscreen()
        self.windows[index] = new_window

    def _create_menu_button(self) -> QtWidgets.QLayout:
        # system_info.is_briefcase_package = lambda: True  # LanguageManager debugging
        settings_menu = MenuButton(
            settings=self.settings,
            language_manager=system_info.is_prebuild_package(),
        )
        settings_menu.com.on_open_url.connect(self.com.on_open_url_and_hide)
        settings_menu.com.on_manage_languages.connect(self.com.on_manage_languages)
        settings_menu.com.on_close_in_settings.connect(
            lambda: self.com.on_close_or_exit.emit("clicked close in menu")
        )
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setRowStretch(1, 1)
        layout.setColumnStretch(0, 1)
        layout.addWidget(settings_menu, 0, 1)
        return layout

    def _update_settings_menu(self, installed_languages: list[str]) -> None:
        """After Language settings changed, recreate menu button the update menus."""
        self._sanatize_active_language(self.settings)

        # TODO: Implement clean way to update the menu than delete & recreate
        menu_layout = self.windows[0].ui_layer.layout()
        if menu_layout:
            while menu_layout.count():
                menu_layout.takeAt(0).widget().deleteLater()
            menu_layout.deleteLater()

        QtCore.QTimer.singleShot(
            5, lambda: self.windows[0].ui_layer.setLayout(self._create_menu_button())
        )

    @staticmethod
    def _sanatize_active_language(settings: QtCore.QSettings) -> None:
        """Verify that languages selected in the settings exist.

        If one doesn't, remove it. If none does, autoselect the first in list.
        """
        installed_languages = ocr.utils.get_tesseract_languages(
            tesseract_cmd=system_info.get_tesseract_path(),
            tessdata_path=system_info.get_tessdata_path(),
        )

        active_languages = settings.value("language")
        if not isinstance(active_languages, list):
            active_languages = [active_languages]

        active_languages = [a for a in active_languages if a in installed_languages]
        if not active_languages:
            active_languages = [installed_languages[0]]

        settings.setValue("language", active_languages)

    #####################
    # OCR Functionality #
    #####################

    @QtCore.Slot(Rect)
    def _crop_image(self, grab_info: tuple[Rect, int]) -> None:
        """Crop image to selected region."""
        logger.info("Crop image to region %s", grab_info[0].points)
        rect, screen_idx = grab_info

        screenshot = self.screens[screen_idx].screenshot
        if not screenshot:
            raise TypeError("Screenshot is None!")

        self.capture.mode = CaptureMode[str(self.settings.value("mode")).upper()]
        self.capture.rect = rect
        self.capture.screen = self.screens[screen_idx]
        self.capture.image = screenshot.copy(QtCore.QRect(*rect.geometry))

        _save_image_in_tempfolder(self.capture.image, postfix="_cropped")

        self.com.on_image_cropped.emit()

    @staticmethod
    def _qimage_to_pil_image(image: QtGui.QImage) -> Image.Image:
        """Cast QImage to pillow Image type."""
        ba = QtCore.QByteArray()
        buffer = QtCore.QBuffer(ba)
        buffer.open(QtCore.QIODevice.ReadWrite)
        image.save(buffer, "PNG")  # type:ignore
        return Image.open(io.BytesIO(buffer.data()))

    @QtCore.Slot()
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
            tesseract_cmd=system_info.get_tesseract_path(),
            languages=language,
            image=self._qimage_to_pil_image(self.capture.image),
            tessdata_path=system_info.get_tessdata_path(),
            parse=self.capture.mode is CaptureMode.PARSE,
            resize_factor=3.2,
            padding_size=80,
        )
        _save_image_in_tempfolder(ocr_result.image, postfix="_enhanced")

        self.capture.ocr_text = ocr_result.text
        self.capture.ocr_applied_magic = ocr_result.best_scored_magic

        logger.info("Text from OCR:\n%s", self.capture.ocr_text)
        self.com.on_ocr_performed.emit()

    @QtCore.Slot(str)
    def _open_url_and_hide(self, url: str) -> None:
        """Open url in default browser, then hide to tray or exit."""
        logger.debug("Open %s", url)
        QtGui.QDesktopServices.openUrl(url)
        self.com.on_close_or_exit.emit("opened web browser")

    @QtCore.Slot()
    def _open_language_manager(self) -> None:
        """Open url in default browser, then hide to tray or exit."""
        logger.debug("Loading language manager...")
        self.language_window = LanguageManager(
            tessdata_path=system_info.config_directory() / "tessdata",
            parent=self.windows[0],
        )
        self.language_window.com.on_open_url.connect(self._open_url_and_hide)
        self.language_window.com.on_change_installed_languages.connect(
            self._update_settings_menu
        )
        self.language_window.exec_()

    @QtCore.Slot()
    def _copy_to_clipboard(self) -> None:
        """Copy results to clipboard."""
        copy_to_clipboard = clipboard.get_copy_func()
        logger.debug("Copy text to clipboard")
        copy_to_clipboard(self.capture.ocr_text)
        self.com.on_copied_to_clipboard.emit()

    @QtCore.Slot()
    def _notify_or_close(self) -> None:
        if self.settings.value("notification", type=bool):
            self.com.on_send_notification.emit(self.capture)
        else:
            self.com.on_close_or_exit.emit("detection completed")

    @QtCore.Slot()
    def _close_windows(self) -> None:
        """Hide all windows of normcap."""
        window_count = len(self.windows)
        if window_count < 1:
            return
        logger.debug("Hide %s window%s", window_count, "s" if window_count > 1 else "")
        QtWidgets.QApplication.restoreOverrideCursor()
        QtWidgets.QApplication.processEvents()
        for window in self.windows.values():
            window.close()
        self.windows = {}

    @QtCore.Slot(str)
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
        logger.info("Exit normcap (%s)", reason)
        logger.debug("Debug images saved in %s%snormcap", tempfile.gettempdir(), os.sep)
        # The preferable QApplication.quit() doesn't work reliably on macOS. E.g. when
        # right clicking on "close" in tray menu, NormCap process keeps running.
        sys.exit(0)
