"""Main entry point for NormCap's UI.

This module hosts most the UI logic. The tray persists from NormCap's start until
the application is closed. Potential windows or other components are started from
here.
"""

# FIXME: Different tray icons are used somewhere! (From system vs. packaged, libnotify)
import logging
import os
import sys
import time
from collections.abc import Iterable
from typing import Any, NoReturn, cast

from PySide6 import QtCore, QtGui, QtNetwork, QtWidgets

from normcap import __version__, clipboard, ocr, screengrab
from normcap.gui import (  # noqa: F401 (loads resources!)
    introduction,
    resources,
    system_info,
    utils,
)
from normcap.gui.language_manager import LanguageManager
from normcap.gui.localization import _
from normcap.gui.menu_button import MenuButton
from normcap.gui.models import Capture, CaptureMode, DesktopEnvironment, Rect, Screen
from normcap.gui.notification import Notifier
from normcap.gui.settings import Settings
from normcap.gui.update_check import UpdateChecker
from normcap.gui.window import Window

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    """TrayMenus' communication bus."""

    exit_application = QtCore.Signal(bool)
    on_copied_to_clipboard = QtCore.Signal()
    on_image_cropped = QtCore.Signal()
    on_region_selected = QtCore.Signal(Rect)
    on_window_positioned = QtCore.Signal()
    on_languages_changed = QtCore.Signal(list)


class SystemTray(QtWidgets.QSystemTrayIcon):
    """System tray icon with menu."""

    _EXIT_DELAY_MILLISECONDS: int = 5_000
    _UPDATE_CHECK_INTERVAL_DAYS: int = 7

    # Only for testing purposes: forcefully enables language manager in settings menu
    # (Normally language manager is only available in pre-build version)
    _testing_language_manager = False

    # Used for singleton:
    _socket_name = f"v{__version__}-normcap"
    _socket_out: QtNetwork.QLocalSocket | None = None
    _socket_in: QtNetwork.QLocalSocket | None = None
    _socket_server: QtNetwork.QLocalServer | None = None

    def __init__(self, parent: QtCore.QObject, args: dict[str, Any]) -> None:
        logger.debug("System info:\n%s", system_info.to_dict())
        super().__init__(parent)

        self.com = Communicate(parent=self)
        self.windows: dict[int, Window] = {}
        self.capture = Capture()
        self.installed_languages: list[str] = []

        self.settings = Settings(init_settings=args)

        if args.get("reset", False):
            self.settings.reset()

        self.cli_mode = args.get("cli_mode", False)
        self.capture.mode = (
            CaptureMode.PARSE
            if self.settings.value("mode") == "parse"
            else CaptureMode.RAW
        )
        self.screens: list[Screen] = system_info.screens()

        self._ensure_screenshot_permission()
        self._set_signals()

        # Needs to be after set signals, cause it might emit self.com.exit_application:
        self._ensure_single_instance()

        self.tray_menu = QtWidgets.QMenu(None)
        self.tray_menu.aboutToShow.connect(self._populate_context_menu_entries)

        self.setContextMenu(self.tray_menu)
        self._populate_context_menu_entries()

        if (
            args.get("show_introduction") is None
            and self.settings.value("show-introduction", type=bool)
        ) or args.get("show_introduction") is True:
            self.show_introduction()
            delay_screenshot = True
        else:
            delay_screenshot = False

        self.reset_tray_icon_timer = QtCore.QTimer(parent=self)
        self.reset_tray_icon_timer.setSingleShot(True)
        self.reset_tray_icon_timer.timeout.connect(self._set_tray_icon)

        self.delayed_exit_timer = QtCore.QTimer(parent=self)
        self.delayed_exit_timer.setSingleShot(True)
        self.delayed_exit_timer.timeout.connect(self.hide)

        self.delayed_init_timer = QtCore.QTimer(parent=self)
        self.delayed_init_timer.setSingleShot(True)
        self.delayed_init_timer.timeout.connect(self._delayed_init)
        self.delayed_init_timer.start(50)

        if not args.get("background_mode", False):
            self._show_windows(delay_screenshot=delay_screenshot)

    def _ensure_single_instance(self) -> None:
        self._socket_out = QtNetwork.QLocalSocket(self)
        self._socket_out.connectToServer(self._socket_name)
        if self._socket_out.waitForConnected():
            logger.debug("Another instance is already running. Sending capture signal.")
            self._socket_out.write(b"capture")
            self._socket_out.waitForBytesWritten(1000)
            self.com.exit_application.emit(False)
        else:
            self._create_socket_server()

    @QtCore.Slot()
    def show_introduction(self) -> None:
        show_intro = bool(self.settings.value("show-introduction", type=bool))
        result = introduction.Dialog(show_on_startup=show_intro).exec()
        if result == introduction.Choice.SHOW:
            self.settings.setValue("show-introduction", True)
        if result == introduction.Choice.DONT_SHOW:
            self.settings.setValue("show-introduction", False)

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

            self.reset_tray_icon_timer.start(5000)

    @QtCore.Slot()
    def _on_new_connection(self) -> None:
        """Open incoming socket to listen for messages from other NormCap instances."""
        if not self._socket_server:
            return
        self._socket_in = self._socket_server.nextPendingConnection()
        if self._socket_in:
            logger.debug("Connect to incoming socket.")
            self._socket_in.readyRead.connect(self._on_ready_read)

    @QtCore.Slot()
    def _on_ready_read(self) -> None:
        """Process messages received from other NormCap instances."""
        if not self._socket_in:
            return
        message = self._socket_in.readAll()
        if message and message.data().decode("utf-8", errors="ignore") == "capture":
            logger.info("Received socket signal to capture.")
            self._show_windows(delay_screenshot=True)

    @QtCore.Slot(QtWidgets.QSystemTrayIcon.ActivationReason)
    def _handle_tray_click(
        self, reason: QtWidgets.QSystemTrayIcon.ActivationReason
    ) -> None:
        logger.debug("Tray event: %s", reason)
        if (
            reason == QtWidgets.QSystemTrayIcon.ActivationReason.Trigger
            and self.settings.value("tray", False, type=bool)
        ):
            self._show_windows(delay_screenshot=True)

    def _show_windows(self, delay_screenshot: bool) -> None:
        """Initialize child windows with method depending on system."""
        screenshots = self._take_screenshots(delay=delay_screenshot)

        if not screenshots:
            logger.error("Could not grab screenshot!")
            return

        for idx, screenshot in enumerate(screenshots):
            self.screens[idx].screenshot = screenshot

        if not system_info.display_manager_is_wayland():
            for index in range(len(system_info.screens())):
                self._create_window(index)

        elif system_info.desktop_environment() in (
            DesktopEnvironment.GNOME,
            DesktopEnvironment.KDE,
            DesktopEnvironment.SWAY,
        ):
            self.com.on_window_positioned.connect(self._create_next_window)
            self._create_next_window()
        else:
            raise RuntimeError("Method for creating window is unspecified!")

    @QtCore.Slot(str)
    def _apply_setting_change(self, setting: str) -> None:
        if setting == "tray":
            capture_action = self.contextMenu().findChild(QtGui.QAction, name="capture")
            capture_action = cast(QtGui.QAction, capture_action)
            is_tray_visible = bool(self.settings.value(setting, False, type=bool))
            capture_action.setVisible(is_tray_visible)

    @QtCore.Slot(list)
    def _sanitize_language_setting(self, installed_languages: list[str]) -> None:
        """Verify that languages selected in the settings exist.

        If one doesn't, remove it. If none does, select the first in list.
        """
        active_languages = self.settings.value("language")
        if not isinstance(active_languages, list):
            active_languages = [active_languages]

        active_languages = [
            a for a in active_languages if a in installed_languages
        ] or [installed_languages[0]]

        self.settings.setValue("language", active_languages)

    @QtCore.Slot(list)
    def _update_installed_languages(self, installed_languages: list[str]) -> None:
        """Update instance attribute to reflect changes.

        the instance attribute is used e.g. to create a menu_button with an up to
        date language menu.
        """
        self.installed_languages = installed_languages

    @QtCore.Slot(Rect)
    def _crop_image(self, grab_info: tuple[Rect, int]) -> None:
        """Crop image to selected region."""
        logger.info("Crop image to region %s", grab_info[0].coords)
        rect, screen_idx = grab_info

        screenshot = self.screens[screen_idx].screenshot
        if not screenshot:
            raise TypeError("Screenshot is None!")

        self.capture.mode = CaptureMode[str(self.settings.value("mode")).upper()]
        self.capture.rect = rect
        self.capture.screen = self.screens[screen_idx]
        self.capture.image = screenshot.copy(QtCore.QRect(*rect.geometry))

        utils.save_image_in_temp_folder(self.capture.image, postfix="_cropped")

        self.com.on_image_cropped.emit()

    @QtCore.Slot()
    def _capture_to_ocr(self) -> None:
        """Perform content recognition on grabbed image."""
        minimum_image_area = 25
        if self.capture.image_area < minimum_image_area:
            logger.warning("Area of %s too small. Skip OCR.", self.capture.image_area)
            self._minimize_or_exit_application(delayed=False)
            return

        logger.debug("Start OCR")
        language = self.settings.value("language")
        if not isinstance(language, str) and not isinstance(language, Iterable):
            raise TypeError()
        ocr_result = ocr.recognize.get_text_from_image(
            tesseract_cmd=system_info.get_tesseract_path(),
            languages=language,
            image=self.capture.image,
            tessdata_path=system_info.get_tessdata_path(),
            parse=self.capture.mode is CaptureMode.PARSE,
            resize_factor=3.2,
            padding_size=80,
        )
        utils.save_image_in_temp_folder(ocr_result.image, postfix="_enhanced")

        self.capture.ocr_text = ocr_result.text
        self.capture.ocr_applied_magic = ocr_result.best_scored_magic

        logger.info("Text from OCR:\n%s", self.capture.ocr_text)
        if self.cli_mode:
            self._print_to_stdout()
        else:
            self._copy_to_clipboard()

    @QtCore.Slot(str)
    def _open_url_and_hide(self, url: str) -> None:
        """Open url in default browser, then hide to tray or exit."""
        logger.debug("Open %s", url)
        result = QtGui.QDesktopServices.openUrl(
            QtCore.QUrl(url, QtCore.QUrl.ParsingMode.TolerantMode)
        )
        logger.debug(f"Opened uri with result={result}")
        self._minimize_or_exit_application(delayed=False)

    @QtCore.Slot()
    def _open_language_manager(self) -> None:
        """Open url in default browser, then hide to tray or exit."""
        logger.debug("Loading language manager...")
        self.language_window = LanguageManager(
            tessdata_path=system_info.config_directory() / "tessdata",
            parent=self.windows[0],
        )
        self.language_window.com.on_open_url.connect(self._open_url_and_hide)
        self.language_window.com.on_languages_changed.connect(
            self.com.on_languages_changed
        )
        self.language_window.exec()

    @QtCore.Slot()
    def _copy_to_clipboard(self) -> None:
        """Copy results to clipboard."""
        copy_to_clipboard = clipboard.get_copy_func()
        logger.debug("Copy text to clipboard")
        copy_to_clipboard(self.capture.ocr_text)
        self.com.on_copied_to_clipboard.emit()

    @QtCore.Slot()
    def _print_to_stdout(self) -> None:
        """Print results to stdout ."""
        logger.debug("Print text to stdout and exit.")
        print(self.capture.ocr_text, file=sys.stdout)  # noqa: T201
        self.com.exit_application.emit(False)

    @QtCore.Slot()
    def _notify(self) -> None:
        if self.settings.value("notification", type=bool):
            self.notifier.com.send_notification.emit(self.capture)

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

    def _delayed_init(self) -> None:
        """Setup things that can be done independent of the first capture.

        By running this async of __init__(),  its runtime of ~30ms doesn't
        contribute to the delay until the GUI becomes active for the user on startup.
        """
        self.notifier = Notifier(parent=self)
        self.installed_languages = ocr.tesseract.get_languages(
            tesseract_cmd=system_info.get_tesseract_path(),
            tessdata_path=system_info.get_tessdata_path(),
        )
        self.com.on_languages_changed.emit(self.installed_languages)
        self._add_update_checker()
        self._set_tray_icon()

    def _set_tray_icon(self) -> None:
        self.setIcon(QtGui.QIcon.fromTheme("tool-magic-symbolic", QtGui.QIcon(":tray")))

    def _create_socket_server(self) -> None:
        """Open socket server to listen for other NormCap instances."""
        if self._socket_out:
            self._socket_out.close()
            self._socket_out = None
        QtNetwork.QLocalServer().removeServer(self._socket_name)
        self._socket_server = QtNetwork.QLocalServer(self)
        self._socket_server.newConnection.connect(self._on_new_connection)
        self._socket_server.listen(self._socket_name)
        logger.debug("Listen on local socket %s.", self._socket_server.serverName())

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
            app = "NormCap" if system_info.is_prebuilt_package() else "Terminal"
            QtWidgets.QMessageBox.critical(
                None,
                _("Error"),
                # L10N: Error message box on macOS only.
                # Do NOT translate the variables in curly brackets "{some_variable}"!
                _(
                    "'{application}' is missing the permission for 'Screen Recording'."
                    "\n\n"
                    "Grant the permission via 'System Settings' > 'Privacy & Security' "
                    "and restart NormCap."
                ).format(application=app),
                buttons=QtWidgets.QMessageBox.StandardButton.Close,
            )
            self.com.exit_application.emit(False)

    def _set_signals(self) -> None:
        """Set up signals to trigger program logic."""
        self.activated.connect(self._handle_tray_click)
        self.com.on_region_selected.connect(self._close_windows)
        self.com.on_region_selected.connect(self._crop_image)
        self.com.on_image_cropped.connect(self._capture_to_ocr)
        self.com.on_copied_to_clipboard.connect(self._notify)
        self.com.on_copied_to_clipboard.connect(
            lambda: self._minimize_or_exit_application(delayed=True)
        )
        self.com.on_copied_to_clipboard.connect(self._color_tray_icon)
        self.com.on_languages_changed.connect(self._sanitize_language_setting)
        self.com.on_languages_changed.connect(self._update_installed_languages)
        self.com.exit_application.connect(self._exit_application)
        self.messageClicked.connect(self._open_language_manager)

    def _add_update_checker(self) -> None:
        if not self.settings.value("update", type=bool):
            return

        now_sub_interval_sec = time.time() - (
            60 * 60 * 24 * self._UPDATE_CHECK_INTERVAL_DAYS
        )
        now_sub_interval = time.strftime("%Y-%m-%d", time.gmtime(now_sub_interval_sec))
        if str(self.settings.value("last-update-check", type=str)) > now_sub_interval:
            return

        checker = UpdateChecker(parent=None, packaged=system_info.is_prebuilt_package())
        checker.com.on_version_checked.connect(self._update_time_of_last_update_check)
        checker.com.on_click_get_new_version.connect(self._open_url_and_hide)
        QtCore.QTimer.singleShot(500, checker.com.check.emit)

    def _update_time_of_last_update_check(self, newest_version: str) -> None:
        if newest_version is not None:
            today = time.strftime("%Y-%m-%d", time.gmtime())
            self.settings.setValue("last-update-check", today)

    @QtCore.Slot()
    def _take_screenshots(self, delay: bool) -> list[QtGui.QImage]:
        """Get new screenshots and cache them."""
        if delay:
            time.sleep(0.15)

        capture = screengrab.get_capture_func()
        screens = capture()

        for idx, screenshot in enumerate(screens):
            utils.save_image_in_temp_folder(screenshot, postfix=f"_raw_screen{idx}")

        return screens

    @QtCore.Slot()
    def _populate_context_menu_entries(self) -> None:
        """Create menu for system tray."""
        self.tray_menu.clear()

        # L10N: Tray menu entry
        action = QtGui.QAction(_("Capture"), self.tray_menu)
        action.setObjectName("capture")
        action.triggered.connect(lambda: self._show_windows(delay_screenshot=True))
        action.setVisible(bool(self.settings.value("tray", False, type=bool)))
        self.tray_menu.addAction(action)

        # L10N: Tray menu entry for exiting NormCap completely.
        action = QtGui.QAction(_("Exit"), self.tray_menu)
        action.setObjectName("exit")
        action.triggered.connect(lambda: self.com.exit_application.emit(False))
        self.tray_menu.addAction(action)

    def _create_next_window(self) -> None:
        """Open child window only for next display."""
        if len(system_info.screens()) > len(self.windows):
            index = len(self.windows.keys())
            self._create_window(index)

    def _create_window(self, index: int) -> None:
        """Open a child window for the specified screen."""
        new_window = Window(
            screen=self.screens[index], settings=self.settings, parent=None
        )
        new_window.com.on_esc_key_pressed.connect(
            lambda: self._minimize_or_exit_application(delayed=False)
        )
        new_window.com.on_esc_key_pressed.connect(
            lambda: self._minimize_or_exit_application(delayed=False)
        )
        new_window.com.on_region_selected.connect(self.com.on_region_selected)
        new_window.com.on_window_positioned.connect(self.com.on_window_positioned)
        if index == 0:
            menu_button = self._create_menu_button()
            layout = self._create_layout()
            layout.addWidget(menu_button, 0, 1)
            new_window.ui_container.setLayout(layout)

        new_window.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        new_window.set_fullscreen()
        self.windows[index] = new_window

    def _create_menu_button(self) -> QtWidgets.QWidget:
        if self._testing_language_manager:
            system_info.is_briefcase_package = lambda: True
        settings_menu = MenuButton(
            settings=self.settings,
            language_manager=system_info.is_prebuilt_package(),
            installed_languages=self.installed_languages,
        )
        settings_menu.com.on_open_url.connect(self._open_url_and_hide)
        settings_menu.com.on_manage_languages.connect(self._open_language_manager)
        settings_menu.com.on_setting_change.connect(self._apply_setting_change)
        settings_menu.com.on_show_introduction.connect(self.show_introduction)
        settings_menu.com.on_close_in_settings.connect(
            lambda: self._minimize_or_exit_application(delayed=False)
        )
        self.com.on_languages_changed.connect(settings_menu.on_languages_changed)
        return settings_menu

    def _create_layout(self) -> QtWidgets.QGridLayout:
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setRowStretch(1, 1)
        layout.setColumnStretch(0, 1)
        return layout

    @QtCore.Slot()
    def _minimize_or_exit_application(self, delayed: bool) -> None:
        self._close_windows()
        if self.settings.value("tray", type=bool):
            return

        self.com.exit_application.emit(delayed)

    @QtCore.Slot(bool)
    def _exit_application(self, delayed: bool) -> None:
        # Unregister the singleton server
        if self._socket_server:
            self._socket_server.close()
            self._socket_server.removeServer(self._socket_name)

        if delayed:
            self.delayed_exit_timer.start(self._EXIT_DELAY_MILLISECONDS)
        else:
            self.hide()

    def hide(self) -> NoReturn | None:
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
        sys.exit(0)
