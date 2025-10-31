"""Start main application logic."""

import json
import logging
import os
import sys
import time
from typing import Any, TypeAlias

from PySide6 import QtCore, QtGui, QtWidgets

from normcap import app_id, clipboard, notification, screenshot
from normcap.detection import detector, ocr
from normcap.detection.models import DetectionMode, DetectionResult
from normcap.gui import (
    constants,
    introduction,
    notification_utils,
    permissions_dialog,
    utils,
)
from normcap.gui.dbus_application_service import DBusApplicationService
from normcap.gui.language_manager import LanguageManager
from normcap.gui.settings import Settings
from normcap.gui.socket_server import SocketServer
from normcap.gui.tray import SystemTray
from normcap.gui.update_check import UpdateChecker
from normcap.gui.window import Window
from normcap.notification.models import ACTION_NAME_NOTIFICATION_CLICKED
from normcap.system import info
from normcap.system.models import Rect, Screen

logger = logging.getLogger(__name__)

Days: TypeAlias = int
Seconds: TypeAlias = float


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

    _EXIT_DELAY_SECONDS: float = 5  # To keep tray icon visible for a while
    _UPDATE_CHECK_INTERVAL_DAYS: int = 7

    # Only for testing purposes: forcefully enables language manager in settings menu
    # (Normally language manager is only available in pre-build version)
    _DEBUG_LANGUAGE_MANAGER = False

    def __init__(self, args: dict[str, Any]) -> None:
        super().__init__()
        self.setQuitOnLastWindowClosed(False)

        # Set application identity for portal recognition
        self.setApplicationName(app_id)
        self.setDesktopFileName(f"{app_id}")

        self.com = Communicate(parent=self)

        # Create DBus Service to listen for notification actions and activations
        self.dbus_service = (
            self._get_dbus_service() if sys.platform == "linux" else None
        )

        # Connect to signals
        if self.dbus_service:
            self.dbus_service.action_activated.connect(self._handle_action_activate)
        self.com.on_exit_application.connect(self._exit_application)
        self.com.on_region_selected.connect(self._start_processing)

        # If NormCap got activated via DBus, only process action then quit.
        if args.get("dbus_activation", False):
            self.com.on_action_finished.connect(
                lambda: self.com.on_exit_application.emit(0)
            )
            # Otherwise exit after timeout
            QtCore.QTimer.singleShot(1000, lambda: self.com.on_exit_application.emit(0))
            return

        # Ensure that only a single instance of NormCap is running.
        self._socket_server = SocketServer()
        if not self._socket_server.is_first_instance:
            self.com.on_exit_application.emit(0)
            return

        self._socket_server.com.on_capture_message.connect(
            lambda: self._show_windows(delay_screenshot=True)
        )

        # Init settings
        self.settings = Settings(init_settings=args)
        if args.get("reset", False):
            self.settings.reset()

        # Init state
        self.screens: list[Screen] = info.screens()
        self.windows: dict[int, Window] = {}
        self.cli_mode = args.get("cli_mode", False)
        self.installed_languages = ["eng"]
        self.screenshot_handler_name = args.get("screenshot_handler")
        self.clipboard_handler_name = args.get("clipboard_handler")
        self.notification_handler_name = args.get("notification_handler")

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
        elif result == introduction.Choice.DONT_SHOW:
            self.settings.setValue("show-introduction", False)

    @QtCore.Slot()
    def show_permissions_info(self) -> None:
        logger.error("Missing screenshot permission!")
        delay = 0

        if sys.platform == "darwin":
            calling_app = "NormCap" if info.is_briefcase_package() else "Terminal"
            text = constants.PERMISSIONS_TEXT_MACOS.format(application=calling_app)

        elif info.is_flatpak():
            text = constants.PERMISSIONS_TEXT_FLATPAK

        elif info.display_manager_is_wayland():
            text = constants.PERMISSIONS_TEXT_WAYLAND

        permissions_dialog.MissingPermissionDialog(text=text).exec()
        self.com.on_exit_application.emit(delay)

    def _get_dbus_service(self) -> DBusApplicationService | None:
        dbus_service = DBusApplicationService(self)
        if not dbus_service.register_service():
            return None

        return dbus_service

    @QtCore.Slot(str, list)
    def _handle_action_activate(
        self, action_name: str, list_of_json: list[str]
    ) -> None:
        text_and_types: list[tuple[str, str]] = json.loads(list_of_json[0])
        logger.info("text_and_types %s", text_and_types)

        if action_name == ACTION_NAME_NOTIFICATION_CLICKED:
            notification_utils.perform_action(texts_and_types=text_and_types)
            self.com.on_action_finished.emit()

    def _verify_screenshot_permission(self) -> None:
        if not self.settings.value("has-screenshot-permission", type=bool):
            if screenshot.has_screenshot_permission(
                request_portal_dialog=permissions_dialog.RequestDbusPermissionDialog
            ):
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
            lambda: self._minimize_to_tray_or_exit(delay=0)
        )
        window.com.on_esc_key_pressed.connect(
            lambda: self._minimize_to_tray_or_exit(delay=0)
        )
        window.com.on_region_selected.connect(self.com.on_region_selected)

        if window.menu_button is not None:
            window.menu_button.com.on_open_url.connect(self._open_url_and_hide)
            window.menu_button.com.on_manage_languages.connect(
                self._open_language_manager
            )
            window.menu_button.com.on_show_introduction.connect(self.show_introduction)
            window.menu_button.com.on_close.connect(
                lambda: self._minimize_to_tray_or_exit(delay=0)
            )

        window.set_fullscreen()
        self.windows[index] = window

    def _show_windows(self, delay_screenshot: bool) -> None:
        """Initialize child windows with method depending on system."""
        if self.windows:
            logger.debug("Capture window(s) already open. Doing nothing.")
            return

        screenshots = self._take_screenshots(delay=delay_screenshot)

        for idx, image in enumerate(screenshots):
            self.screens[idx].screenshot = image

        for index in range(len(info.screens())):
            self._create_window(index)

    @QtCore.Slot()
    def _close_windows(self) -> None:
        """Hide all windows of normcap."""
        window_count = len(self.windows)
        if window_count < 1:
            return
        logger.debug("Hide %s window%s", window_count, "s" if window_count > 1 else "")
        self.restoreOverrideCursor()
        for window in self.windows.values():
            QtCore.QTimer.singleShot(0, window.close)
            self.processEvents()

        self.windows = {}
        self.com.on_windows_closed.emit()

    def _is_time_for_update_check(self) -> bool:
        """Test if the time of last update exceeds the days of update interval."""
        seconds_per_day = 60 * 60 * 24
        update_interval_seconds = seconds_per_day * self._UPDATE_CHECK_INTERVAL_DAYS

        cutoff_date = time.gmtime(time.time() - update_interval_seconds)
        cutoff_date_str = time.strftime(constants.DATE_FORMAT, cutoff_date)

        last_check_date_str = str(self.settings.value("last-update-check", type=str))

        return last_check_date_str > cutoff_date_str

    def _add_update_checker(self) -> None:
        if not self.settings.value("update", type=bool):
            return

        if not self._is_time_for_update_check():
            return

        self.checker = UpdateChecker(packaged=info.is_packaged())
        self.checker.com.on_version_checked.connect(self._set_last_update_check_time)
        self.checker.com.on_click_get_new_version.connect(self._open_url_and_hide)

        QtCore.QTimer.singleShot(500, self.checker.check_for_updates)

    def _set_last_update_check_time(self, newest_version: str) -> None:
        if newest_version is not None:
            today = time.strftime(constants.DATE_FORMAT, time.gmtime())
            self.settings.setValue("last-update-check", today)

    @QtCore.Slot(str)
    def _open_url_and_hide(self, url: str) -> None:
        """Open url in default browser, then hide to tray or exit."""
        logger.debug("Open %s", url)
        result = QtGui.QDesktopServices.openUrl(
            QtCore.QUrl(url, QtCore.QUrl.ParsingMode.TolerantMode)
        )
        logger.debug("Opened uri with result=%s", result)
        self._minimize_to_tray_or_exit(delay=0)

    @QtCore.Slot()
    def _start_processing(self, rect: Rect, screen_idx: int) -> None:
        self._close_windows()

        QtCore.QTimer.singleShot(
            20, lambda: self._run_detection(rect=rect, screen_idx=screen_idx)
        )

    @QtCore.Slot()
    def _run_detection(self, rect: Rect, screen_idx: int) -> None:
        """Crop screenshot, perform content recognition on it and process result."""
        cropped_screenshot = utils.crop_image(
            image=self.screens[screen_idx].screenshot, rect=rect
        )

        minimum_image_area = 100
        image_area = cropped_screenshot.width() * cropped_screenshot.height()
        if image_area < minimum_image_area:
            logger.warning("Area of %spx is too small. Skip detection.", image_area)
            self._minimize_to_tray_or_exit(delay=0)
            return

        tessdata_path = info.get_tessdata_path(
            config_directory=info.config_directory(),
            is_packaged=info.is_packaged(),
        )
        tesseract_bin_path = info.get_tesseract_bin_path(
            is_briefcase_package=info.is_briefcase_package()
        )

        detection_mode = DetectionMode(0)
        if bool(self.settings.value("detect-codes", type=bool)):
            detection_mode |= DetectionMode.CODES
        if bool(self.settings.value("detect-text", type=bool)):
            detection_mode |= DetectionMode.TESSERACT

        results = detector.detect(
            image=cropped_screenshot,
            tesseract_bin_path=tesseract_bin_path,
            tessdata_path=tessdata_path,
            language=self.settings.value("language"),
            detect_mode=detection_mode,
            parse_text=bool(self.settings.value("parse-text", type=bool)),
        )

        result_text = os.linesep.join(r.text for r in results)

        if result_text and self.cli_mode:
            self._print_to_stdout_and_exit(text=result_text)
        elif result_text:
            self._copy_to_clipboard(text=result_text)
        else:
            logger.warning("Nothing detected on selected region.")

        if self.settings.value("notification", type=bool):
            self._send_notification(detection_results=results)

        self._minimize_to_tray_or_exit(delay=self._EXIT_DELAY_SECONDS)
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

    def _send_notification(self, detection_results: list[DetectionResult]) -> None:
        title = notification_utils.get_title(detection_results=detection_results)
        message = notification_utils.get_text(detection_results=detection_results)
        actions = notification_utils.get_actions(
            detection_results=detection_results,
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
            tesseract_cmd=info.get_tesseract_bin_path(
                is_briefcase_package=info.is_briefcase_package()
            ),
            tessdata_path=info.get_tessdata_path(
                config_directory=info.config_directory(),
                is_packaged=info.is_packaged(),
            ),
        )
        self._sanitize_language_setting()

    @QtCore.Slot()
    def _open_language_manager(self) -> None:
        """Open url in default browser, then hide to tray or exit."""
        logger.debug("Loading language manager …")
        self.language_window = LanguageManager(
            tessdata_path=info.config_directory() / "tessdata",
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

    @QtCore.Slot(bool)
    def _exit_application(self, delay: Seconds = 0) -> None:
        if delay:
            QtCore.QTimer.singleShot(int(delay * 1000), self._exit_application)
            return

        if hasattr(self, "tray"):
            # Hide avoids having the icon dangling in system tray for a few seconds
            # (Tray wasn't created if another instance was already running)
            self.tray.hide()

        if hasattr(self, "_socket_server"):
            self._socket_server.close()

        logger.info("Exit normcap")
        logger.debug("Debug images in %s%snormcap", utils.tempfile.gettempdir(), os.sep)

        # Not sure why, but quit doesn't work reliably if called directly
        QtCore.QTimer.singleShot(0, lambda: self.quit())

        # Use harsher fallback if quit() didn't work
        QtCore.QTimer.singleShot(500, lambda: sys.exit(1))

    @QtCore.Slot()
    def _minimize_to_tray_or_exit(self, delay: Seconds) -> None:
        self._close_windows()
        if self.settings.value("tray", type=bool):
            return

        self.com.on_exit_application.emit(delay)
