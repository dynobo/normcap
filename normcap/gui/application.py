"""Start main application logic."""

import logging
import os
import sys
import time
from typing import Any

from PySide6 import QtCore, QtGui, QtNetwork, QtWidgets

from normcap import __version__, clipboard, notification, screenshot
from normcap.detection import detector, ocr
from normcap.detection.models import DetectionMode, TextDetector, TextType
from normcap.gui import (
    constants,
    introduction,
    notification_utils,
    permissions_dialog,
    system_info,
    utils,
)
from normcap.gui.constants import APP_ID
from normcap.gui.dbus_application_service import DBusApplicationService
from normcap.gui.language_manager import LanguageManager
from normcap.gui.models import Days, Rect, Screen, Seconds
from normcap.gui.settings import Settings
from normcap.gui.tray import SystemTray
from normcap.gui.update_check import UpdateChecker
from normcap.gui.window import Window
from normcap.notification.models import ACTION_NAME_NOTIFICATION_CLICKED

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    """Application's communication bus."""

    on_exit_application = QtCore.Signal(float)
    on_copied_to_clipboard = QtCore.Signal()
    on_region_selected = QtCore.Signal(Rect, int)
    on_action_finished = QtCore.Signal()
    on_windows_closed = QtCore.Signal()


class NormcapApp(QtWidgets.QApplication):
    """Main NormCap application logic."""

    # Used for singleton:
    _socket_name = f"v{__version__}-normcap"
    _socket_out: QtNetwork.QLocalSocket | None = None
    _socket_in: QtNetwork.QLocalSocket | None = None
    _socket_server: QtNetwork.QLocalServer | None = None

    _EXIT_DELAY: Seconds = 5  # To keep tray icon visible for a while
    _UPDATE_CHECK_INTERVAL: Days = 7

    # Only for testing purposes: forcefully enables language manager in settings menu
    # (Normally language manager is only available in pre-build version)
    _DEBUG_LANGUAGE_MANAGER = False

    def __init__(self, args: dict[str, Any]) -> None:
        super().__init__()
        self.setQuitOnLastWindowClosed(False)

        # Set application identity for portal recognition
        self.setApplicationName(APP_ID)
        self.setDesktopFileName(f"{APP_ID}.desktop")

        self.com = Communicate(parent=self)

        # Create DBus Service to listen for notification actions and activations
        self.dbus_service = (
            self._get_dbus_service() if system_info.is_flatpak() else None
        )

        # Connect to signals
        if self.dbus_service:
            self.dbus_service.action_activated.connect(self._handle_action_activate)
        self.com.on_exit_application.connect(self._exit_application)
        self.com.on_region_selected.connect(self._close_windows)
        self.com.on_region_selected.connect(self._trigger_detect)

        # Ensure that only a single instance of NormCap is running.
        if self._other_instance_is_running():
            self.com.on_exit_application.emit(0)
            return

        # Start listening to socket for other instances
        self._create_socket_server()

        # Init settings
        self.settings = Settings(init_settings=args)
        if args.get("reset", False):
            self.settings.reset()

        # Init state
        self.screens: list[Screen] = system_info.screens()
        self.windows: dict[int, Window] = {}
        self.cli_mode = args.get("cli_mode", False)
        self.installed_languages = ["eng"]
        self.screenshot_handler_name = args.get("screenshot_handler")
        self.clipboard_handler_name = args.get("clipboard_handler")
        self.notification_handler_name = args.get("notification_handler")

        # TODO: Move more to top?
        if args.get("dbus_activation", False):
            # Skip UI setup. Just wait for ActionActivate signal to happen the exit
            self.com.on_action_finished.connect(
                lambda: self.com.on_exit_application.emit(0)
            )
            # Otherwise exit after timeout
            QtCore.QTimer.singleShot(1000, lambda: self.com.on_exit_application.emit(0))
            return

        # Check if have screenshot permission and try to request if needed
        self._verify_screenshot_permission()

        # Show intro (and delay screenshot to not capute the intro)
        if (
            args.get("show_introduction") is None
            and self.settings.value("show-introduction", type=bool)
        ) or args.get("show_introduction") is True:
            self.show_introduction()
            delay_screenshot = True
        else:
            delay_screenshot = False

        # Show main UI
        if not args.get("background_mode", False):
            self._show_windows(delay_screenshot=delay_screenshot)

        # Show system tray
        self.tray = SystemTray(
            self, keep_in_tray=bool(self.settings.value("tray", False, type=bool))
        )
        self.tray.com.on_tray_clicked.connect(
            lambda: self._show_windows(delay_screenshot=True)
        )
        self.tray.com.on_menu_exit_clicked.connect(
            lambda: self.com.on_exit_application.emit(0)
        )
        self.tray.com.on_menu_capture_clicked.connect(
            lambda: self._show_windows(delay_screenshot=True)
        )
        self.settings.com.on_value_changed.connect(self.tray.apply_setting_change)
        self.tray.show()

        # Defer non-crucial init to faster be interactive
        QtCore.QTimer.singleShot(50, self._delayed_init)

    @QtCore.Slot()
    def show_introduction(self) -> None:
        show_intro = bool(self.settings.value("show-introduction", type=bool))
        result = introduction.IntroductionDialog(
            show_on_startup=show_intro,
            parent=self.windows[0] if self.windows else None,
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

        elif system_info.is_flatpak():
            text = constants.PERMISSIONS_TEXT_FLATPAK

        elif system_info.display_manager_is_wayland():
            text = constants.PERMISSIONS_TEXT_WAYLAND

        permissions_dialog.PermissionDialog(text=text).exec()
        self.com.on_exit_application.emit(delay)

    def _get_dbus_service(self) -> DBusApplicationService | None:
        dbus_service = DBusApplicationService(self)
        if not dbus_service.register_service():
            logger.error("Failed to register DBus activation service")
            return None

        logger.debug("Registered DBus activation service")
        return dbus_service

    @QtCore.Slot(str, list)
    def _handle_action_activate(self, action_name: str, parameter: list) -> None:
        if action_name == ACTION_NAME_NOTIFICATION_CLICKED:
            text, text_type = parameter
            notification_utils.perform_action(text=text, text_type=text_type)
            self.com.on_action_finished.emit()

    def _verify_screenshot_permission(self) -> None:
        if not self.settings.value("has-screenshot-permission", type=bool):
            if screenshot.has_screenshot_permission():
                self.settings.setValue("has-screenshot-permission", True)
            else:
                self.show_permissions_info()

    def _create_window(self, index: int) -> None:
        """Open a child window for the specified screen."""
        window = Window(
            screen=self.screens[index],
            index=index,
            settings=self.settings,
            installed_languages=self.installed_languages,
            debug_language_manager=self._DEBUG_LANGUAGE_MANAGER,
        )
        window.com.on_esc_key_pressed.connect(
            lambda: self._minimize_or_exit_application(delay=0)
        )
        window.com.on_esc_key_pressed.connect(
            lambda: self._minimize_or_exit_application(delay=0)
        )
        window.com.on_region_selected.connect(self.com.on_region_selected)

        if window.menu_button is not None:
            window.menu_button.com.on_open_url.connect(self._open_url_and_hide)
            window.menu_button.com.on_manage_languages.connect(
                self._open_language_manager
            )
            window.menu_button.com.on_show_introduction.connect(self.show_introduction)
            window.menu_button.com.on_close.connect(
                lambda: self._minimize_or_exit_application(delay=0)
            )

        window.set_fullscreen()
        self.windows[index] = window

    def _show_windows(self, delay_screenshot: bool) -> None:
        """Initialize child windows with method depending on system."""
        screenshots = self._take_screenshots(delay=delay_screenshot)

        for idx, image in enumerate(screenshots):
            self.screens[idx].screenshot = image

        for index in range(len(system_info.screens())):
            self._create_window(index)

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
        self.com.on_windows_closed.emit()

    def _add_update_checker(self) -> None:
        if not self.settings.value("update", type=bool):
            return

        now_sub_interval_sec = time.time() - (
            60 * 60 * 24 * self._UPDATE_CHECK_INTERVAL
        )
        now_sub_interval = time.strftime("%Y-%m-%d", time.gmtime(now_sub_interval_sec))
        if str(self.settings.value("last-update-check", type=str)) > now_sub_interval:
            return

        self.checker = UpdateChecker(
            parent=None, packaged=system_info.is_prebuilt_package()
        )
        self.checker.com.on_version_checked.connect(
            self._update_time_of_last_update_check
        )
        self.checker.com.on_click_get_new_version.connect(self._open_url_and_hide)
        # TODO: Trigger check via checker.com signal?
        QtCore.QTimer.singleShot(500, self.checker.com.check.emit)

    def _update_time_of_last_update_check(self, newest_version: str) -> None:
        if newest_version is not None:
            today = time.strftime("%Y-%m-%d", time.gmtime())
            self.settings.setValue("last-update-check", today)

    @QtCore.Slot(str)
    def _open_url_and_hide(self, url: str) -> None:
        """Open url in default browser, then hide to tray or exit."""
        logger.debug("Open %s", url)
        result = QtGui.QDesktopServices.openUrl(
            QtCore.QUrl(url, QtCore.QUrl.ParsingMode.TolerantMode)
        )
        logger.debug("Opened uri with result=%s", result)
        self._minimize_or_exit_application(delay=0)

    @QtCore.Slot()
    def _trigger_detect(self, rect: Rect, screen_idx: int) -> None:
        """Crop screenshot, perform content recognition on it and process result."""
        cropped_screenshot = utils.crop_image(
            image=self.screens[screen_idx].screenshot, rect=rect
        )

        minimum_image_area = 100
        image_area = cropped_screenshot.width() * cropped_screenshot.height()
        if image_area < minimum_image_area:
            logger.warning("Area of %spx is too small. Skip detection.", image_area)
            self._minimize_or_exit_application(delay=0)
            return

        tessdata_path = system_info.get_tessdata_path(
            config_directory=system_info.config_directory(),
            is_flatpak_package=system_info.is_flatpak(),
            is_briefcase_package=system_info.is_briefcase_package(),
        )
        tesseract_bin_path = system_info.get_tesseract_bin_path(
            is_briefcase_package=system_info.is_briefcase_package()
        )

        detection_mode = DetectionMode(0)
        if bool(self.settings.value("detect-codes", type=bool)):
            detection_mode |= DetectionMode.CODES
        if bool(self.settings.value("detect-text", type=bool)):
            detection_mode |= DetectionMode.TESSERACT

        result = detector.detect(
            image=cropped_screenshot,
            tesseract_bin_path=tesseract_bin_path,
            tessdata_path=tessdata_path,
            language=self.settings.value("language"),
            detect_mode=detection_mode,
            parse_text=bool(self.settings.value("parse-text", type=bool)),
        )

        if result.text and self.cli_mode:
            self._print_to_stdout_and_exit(text=result.text)
        elif result.text:
            self._copy_to_clipboard(text=result.text)
        else:
            logger.warning("Nothing detected on selected region.")

        if self.settings.value("notification", type=bool):
            self._send_notification(
                text=result.text, text_type=result.text_type, detector=result.detector
            )

        self._minimize_or_exit_application(delay=self._EXIT_DELAY)
        self.tray.show_completion_icon()

    def _copy_to_clipboard(self, text: str) -> None:
        """Copy results to clipboard."""
        if self.clipboard_handler_name:
            logger.debug(
                "Copy text to clipboard with %s",
                self.clipboard_handler_name.upper(),
            )
            clipboard.copy_with_handler(
                text=text, handler_name=self.clipboard_handler_name
            )
        else:
            logger.debug("Copy text to clipboard")
            clipboard.copy(text=text)
        self.com.on_copied_to_clipboard.emit()

    @QtCore.Slot(str)
    def _print_to_stdout_and_exit(self, text: str) -> None:
        """Print results to stdout ."""
        logger.debug("Print text to stdout and exit.")
        print(text, file=sys.stdout)  # noqa: T201
        self.com.on_exit_application.emit(0)

    def _send_notification(
        self, text: str, text_type: TextType, detector: TextDetector
    ) -> None:
        title = notification_utils.get_title(
            text=text, text_type=text_type, detector=detector
        )
        message = notification_utils.get_text(text=text)
        actions = notification_utils.get_actions(
            text=text,
            text_type=text_type,
            action_func=self._handle_action_activate,
        )

        notification.notify(
            title=title,
            message=message,
            actions=actions,
            handler_name=self.notification_handler_name,
        )

    @QtCore.Slot()
    def _take_screenshots(self, delay: bool) -> list[QtGui.QImage]:
        """Get new screenshots and cache them."""
        if delay:
            # Timeout should be high enough for visible windows to completely hide and
            # short enough to not annoy the users to much. (FTR: 0.15 was too short.)
            time.sleep(0.5)

        if self.screenshot_handler_name:
            logger.debug(
                "Take screenshot explicitly with %s",
                self.screenshot_handler_name.upper(),
            )
            screens = screenshot.capture_with_handler(
                handler_name=self.screenshot_handler_name
            )
        else:
            screens = screenshot.capture()

        if not screens:
            self.settings.setValue("has-screenshot-permission", False)
            raise RuntimeError("No screenshot taken!")

        for idx, image in enumerate(screens):
            utils.save_image_in_temp_folder(image, postfix=f"_raw_screen{idx}")

        return screens

    def _delayed_init(self) -> None:
        """Setup things that can be done independent of the first capture.

        By running this async of __init__(),  its runtime of ~30ms doesn't
        contribute to the delay until the GUI becomes active for the user on startup.
        """
        self._add_update_checker()
        self._update_installed_languages()

    def _update_installed_languages(self) -> None:
        self.installed_languages = ocr.tesseract.get_languages(
            tesseract_cmd=system_info.get_tesseract_bin_path(
                is_briefcase_package=system_info.is_briefcase_package()
            ),
            tessdata_path=system_info.get_tessdata_path(
                config_directory=system_info.config_directory(),
                is_briefcase_package=system_info.is_briefcase_package(),
                is_flatpak_package=system_info.is_flatpak(),
            ),
        )
        self._sanitize_language_setting()

    @QtCore.Slot()
    def _open_language_manager(self) -> None:
        """Open url in default browser, then hide to tray or exit."""
        logger.debug("Loading language manager …")
        self.language_window = LanguageManager(
            tessdata_path=system_info.config_directory() / "tessdata",
            parent=self.windows[0],
        )
        self.language_window.com.on_open_url.connect(self._open_url_and_hide)
        self.language_window.com.on_languages_changed.connect(
            self._update_installed_languages
        )
        self.language_window.exec()

    @QtCore.Slot(list)
    def _sanitize_language_setting(
        self,
    ) -> None:
        """Verify that languages selected in the settings exist.

        If one doesn't, remove it. If none does, select the first in list.
        """
        active_languages = self.settings.value("language")
        if not isinstance(active_languages, list):
            active_languages = [active_languages]

        active_languages = [
            a for a in active_languages if a in self.installed_languages
        ] or [self.installed_languages[0]]

        self.settings.setValue("language", active_languages)

    def _other_instance_is_running(self) -> bool:
        """Test if connection to another NormCap instance socket can be established."""
        self._socket_out = QtNetwork.QLocalSocket(self)
        self._socket_out.connectToServer(self._socket_name)
        if self._socket_out.waitForConnected():
            logger.debug("Another instance is already running. Sending capture signal.")
            self._socket_out.write(b"capture")
            self._socket_out.waitForBytesWritten(1000)
            return True

        return False

    # TODO: Carve out socket logic into own module?
    def _create_socket_server(self) -> None:
        """Open socket server to listen for other NormCap instances."""
        if self._socket_out:
            self._socket_out.close()
            self._socket_out = None
        QtNetwork.QLocalServer().removeServer(self._socket_name)
        self._socket_server = QtNetwork.QLocalServer(self)
        self._socket_server.newConnection.connect(self._on_socket_connect)
        self._socket_server.listen(self._socket_name)
        logger.debug("Listen on local socket %s.", self._socket_server.serverName())

    @QtCore.Slot()
    def _on_socket_connect(self) -> None:
        """Open incoming socket to listen for messages from other NormCap instances."""
        if not self._socket_server:
            return
        self._socket_in = self._socket_server.nextPendingConnection()
        if self._socket_in:
            logger.debug("Connect to incoming socket.")
            self._socket_in.readyRead.connect(self._on_socket_ready_read)

    @QtCore.Slot()
    def _on_socket_ready_read(self) -> None:
        """Process messages received from other NormCap instances."""
        if not self._socket_in:
            return

        message = self._socket_in.readAll().data().decode("utf-8", errors="ignore")
        if message != "capture":
            return

        logger.info("Received socket signal to capture.")
        if self.windows:
            logger.debug("Capture window(s) already open. Doing nothing.")
            return

        self._show_windows(delay_screenshot=True)

    @QtCore.Slot(bool)
    def _exit_application(self, delay: Seconds = 0) -> None:
        # Unregister the singleton server
        if self._socket_server:
            self._socket_server.close()
            self._socket_server.removeServer(self._socket_name)
            self._socket_server = None

        if delay:
            QtCore.QTimer.singleShot(int(delay * 1000), self._exit_application)
        else:
            self.tray.hide()
            logger.info("Exit normcap")
            logger.debug(
                "Debug images saved in %s%snormcap", utils.tempfile.gettempdir(), os.sep
            )
            self.exit(0)

    @QtCore.Slot()
    def _minimize_or_exit_application(self, delay: Seconds) -> None:
        self._close_windows()
        if self.settings.value("tray", type=bool):
            return

        self.com.on_exit_application.emit(delay)
