"""Start main application logic."""

import logging
import sys
import time
from typing import Any

from PySide6 import QtCore, QtGui, QtNetwork, QtWidgets

from normcap import __version__, clipboard, notification, screenshot
from normcap.detection import detector
from normcap.detection.models import DetectionMode, TextDetector, TextType
from normcap.gui import notification_utils, system_info, utils
from normcap.gui.menu_button import MenuButton
from normcap.gui.models import Days, Rect, Screen, Seconds
from normcap.gui.settings import Settings
from normcap.gui.tray import SystemTray
from normcap.gui.window import Window

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    """TrayMenus' communication bus."""

    on_exit_application = QtCore.Signal(float)
    on_copied_to_clipboard = QtCore.Signal()
    on_region_selected = QtCore.Signal(Rect, int)
    on_languages_changed = QtCore.Signal(list)
    on_action_finished = QtCore.Signal()
    on_windows_closed = QtCore.Signal()


class Timers:
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        self.delayed_exit = QtCore.QTimer(parent=parent, singleShot=True)
        self.delayed_detectation = QtCore.QTimer(parent=parent, singleShot=True)


class NormcapApp(QtWidgets.QApplication):
    """Main NormCap application logic."""

    # Used for singleton:
    _socket_name = f"v{__version__}-normcap"
    _socket_out: QtNetwork.QLocalSocket | None = None
    _socket_in: QtNetwork.QLocalSocket | None = None
    _socket_server: QtNetwork.QLocalServer | None = None

    _EXIT_DELAY: Seconds = 5
    _UPDATE_CHECK_INTERVAL: Days = 7

    # Only for testing purposes: forcefully enables language manager in settings menu
    # (Normally language manager is only available in pre-build version)
    _TESTING_LANGUAGE_MANAGER = False

    def __init__(self, args: dict[str, Any]) -> None:
        super().__init__()
        self.setQuitOnLastWindowClosed(False)

        self.com = Communicate(parent=self)
        self.timers = Timers(parent=self)
        self.timers.delayed_exit.timeout.connect(self._exit_application)

        # Connect to signals
        self.com.on_exit_application.connect(self._exit_application)

        # Ensure that only a single instance of NormCap is running.
        if self._other_instance_is_running():
            self.com.on_exit_application.emit(0)
            return

        # Start listening to socket for other instances
        self._create_socket_server()

        # Perform settings reset
        if args.get("reset", False):
            self.settings.reset()

        # Init state
        self.settings = Settings(init_settings=args)
        self.screens: list[Screen] = system_info.screens()
        self.windows: dict[int, Window] = {}
        self.installed_languages: list[str] = []
        self.cli_mode = args.get("cli_mode", False)
        self.screenshot_handler_name = args.get("screenshot_handler")
        self.clipboard_handler_name = args.get("clipboard_handler")
        self.notification_handler_name = args.get("notification_handler")

        # Run main logic
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
        self.tray = SystemTray(self, args)
        self.tray.show()

    def _verify_screenshot_permission(self) -> None:
        if not self.settings.value("has-screenshot-permission", type=bool):
            if screenshot.has_screenshot_permission():
                self.settings.setValue("has-screenshot-permission", True)
            else:
                self.show_permissions_info()

    def _create_window(self, index: int) -> None:
        """Open a child window for the specified screen."""
        new_window = Window(
            screen=self.screens[index], settings=self.settings, parent=None
        )
        new_window.com.on_esc_key_pressed.connect(
            lambda: self.tray._minimize_or_exit_application(delay=0)
        )
        new_window.com.on_esc_key_pressed.connect(
            lambda: self.tray._minimize_or_exit_application(delay=0)
        )
        new_window.com.on_region_selected.connect(self.com.on_region_selected)
        if index == 0:
            # TODO: Move to window?
            menu_button = self._create_menu_button()
            layout = self._create_layout()
            layout.addWidget(menu_button, 0, 1)
            new_window.ui_container.setLayout(layout)

        new_window.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        new_window.set_fullscreen()
        self.windows[index] = new_window

    # TODO: Move create menu logix to window?
    def _create_menu_button(self) -> QtWidgets.QWidget:
        if self._TESTING_LANGUAGE_MANAGER:
            system_info.is_briefcase_package = lambda: True
        settings_menu = MenuButton(
            settings=self.settings,
            language_manager=system_info.is_prebuilt_package(),
            installed_languages=self.installed_languages,
        )
        settings_menu.com.on_open_url.connect(self.tray._open_url_and_hide)
        settings_menu.com.on_manage_languages.connect(self.tray._open_language_manager)
        settings_menu.com.on_setting_change.connect(self.tray._apply_setting_change)
        settings_menu.com.on_show_introduction.connect(self.tray.show_introduction)
        settings_menu.com.on_close_in_settings.connect(
            lambda: self.tray._minimize_or_exit_application(delay=0)
        )
        self.com.on_languages_changed.connect(settings_menu.on_languages_changed)
        return settings_menu

    # TODO: Move to window
    @staticmethod
    def _create_layout() -> QtWidgets.QGridLayout:
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setRowStretch(1, 1)
        layout.setColumnStretch(0, 1)
        return layout

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

    @QtCore.Slot()
    def _schedule_detection(self, rect: Rect, screen_idx: int) -> None:
        """Schedule detection to run after window closing is complete."""
        # Use a single-shot timer to defer detection execution
        # TODO: Is this required?
        self.timers.delayed_detectation.timeout.connect(
            lambda: self._trigger_detect(rect, screen_idx)
        )
        self.timers.delayed_detectation.start(1)

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
            self.tray._minimize_or_exit_application(delay=0)
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

        self.tray._minimize_or_exit_application(delay=self._EXIT_DELAY)
        self.tray._set_tray_icon_done()

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
            action_func=self.tray._handle_action_activate,
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
        if self.tray.windows:
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
            self.timers.delayed_exit.start(int(delay * 1000))
        else:
            self.tray.hide()
            self.exit(0)
