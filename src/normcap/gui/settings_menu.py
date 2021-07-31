"""Create the settings button and its menu."""

from PySide2 import QtCore, QtGui, QtWidgets

from normcap.models import URLS, Platform
from normcap.utils import get_icon, open_url_and_hide


class SettingsMenu(QtWidgets.QMenu):
    """Settings menu and bindings to actions."""

    style_sheet = """
            QMenu {
                background-color: rgba(0,0,0,0.8);
                color: white;
            }
            QMenu::separator {
                background-color: rgba(255,255,255,0.2);
                height: 1px;
                margin-top: 5px;
            }
            QMenu::item {
                padding: 3px 16px 3px 16px;
                background-color: transparent;
            }
            QMenu::item:disabled {
                color: $COLOR;
            }
            QMenu::item:selected {
                background-color: rgba(150,150,150,0.5);
            }
            QMenu::indicator {
                position: relative;
                right: -5px;
            }
            QMenu::indicator:unchecked {
            }
            QMenu::indicator:checked {
            }
            QMenu::left-arrow,
            QMenu::right-arrow {
                margin: 5px;
            }
        """

    def __init__(self, parent: QtWidgets.QWidget, window_main: QtWidgets.QMainWindow):
        super().__init__(parent)
        self.setObjectName("settings_menu")
        self.window_main = window_main

        self.setStyleSheet(self.style_sheet.replace("$COLOR", window_main.config.color))
        self.title_font = self.get_title_font()

        self.add_title("Settings")
        self.add_settings_section()
        self.addSeparator()
        self.add_title("Capture mode")
        self.add_mode_section()
        self.addSeparator()
        self.add_title("Languages")
        self.add_languages_section()
        self.addSeparator()
        self.add_title("Application")
        self.add_application_section()

    @staticmethod
    def get_title_font() -> QtGui.QFont:
        """Define font for menu subtitles."""
        font = QtGui.QFont()
        font.setPixelSize(12)
        font.setBold(True)
        return font

    def add_title(self, title: str):
        """Add section title."""
        action = QtWidgets.QAction(title, self)
        action.setEnabled(False)
        action.setFont(self.title_font)
        self.addAction(action)

    def add_settings_section(self):
        """Add session options and actions."""
        # pylint: disable=no-member  # action.triggered.connect is not resolved

        action = QtWidgets.QAction("Show notifications", self)
        action.setCheckable(True)
        action.setChecked(self.window_main.config.notifications)
        action.triggered.connect(
            lambda check: self.window_main.set_config("notifications", check)
        )
        self.addAction(action)

        action = QtWidgets.QAction("Keep in system tray", self)
        action.setCheckable(True)
        action.setChecked(self.window_main.config.tray)
        action.triggered.connect(
            lambda check: self.window_main.set_config("tray", check)
        )
        self.addAction(action)

        action = QtWidgets.QAction("Check for updates", self)
        action.setCheckable(True)
        action.setChecked(self.window_main.config.updates)
        action.triggered.connect(
            lambda check: self.window_main.set_config("updates", check)
        )
        self.addAction(action)

    def add_mode_section(self):
        """Add caputure mode options and actions."""
        # pylint: disable=no-member
        mode_group = QtWidgets.QActionGroup(self)
        mode_group.setExclusive(True)
        action = QtWidgets.QAction("parse", self)
        action.setCheckable(True)
        action.triggered.connect(
            lambda check=True, mode="parse": self.window_main.set_config("mode", mode)
        )
        action.setChecked(self.window_main.config.mode == "parse")
        mode_group.addAction(action)
        self.addAction(action)

        action = QtWidgets.QAction("raw", self)
        action.setCheckable(True)
        action.triggered.connect(
            lambda check=True, mode="raw": self.window_main.set_config("mode", mode)
        )
        action.setChecked(self.window_main.config.mode == "raw")
        mode_group.addAction(action)
        self.addAction(action)

    def add_languages_section(self):
        """Add multiselect for language option."""
        # pylint: disable=no-member
        for language in self.window_main.system_info.tesseract_languages:
            action = QtWidgets.QAction(language, self)
            action.setCheckable(True)
            action.triggered.connect(
                lambda check=True, language=language: self.window_main.set_config(
                    "languages", language
                )
            )
            action.setChecked(language in self.window_main.config.languages)
            self.addAction(action)

    def add_application_section(self):
        """Add application related actions."""
        # pylint: disable=no-member

        submenu = QtWidgets.QMenu(self)
        submenu.setObjectName("settings_menu_website")
        submenu.setTitle("Website")

        action = QtWidgets.QAction("Source code", submenu)
        action.triggered.connect(
            lambda: open_url_and_hide(self.window_main, URLS.github)
        )
        submenu.addAction(action)

        action = QtWidgets.QAction("Releases", submenu)
        action.triggered.connect(
            lambda: open_url_and_hide(self.window_main, URLS.releases)
        )
        submenu.addAction(action)

        action = QtWidgets.QAction("FAQ", submenu)
        action.triggered.connect(lambda: open_url_and_hide(self.window_main, URLS.faqs))
        submenu.addAction(action)

        action = QtWidgets.QAction("Report a problem", submenu)
        action.triggered.connect(
            lambda: open_url_and_hide(self.window_main, URLS.issues)
        )
        submenu.addAction(action)

        self.addMenu(submenu)

        action = QtWidgets.QAction("Close", self)
        action.triggered.connect(self.window_main.com.onQuitOrHide.emit)
        self.addAction(action)


class SettingsButton(QtWidgets.QToolButton):
    """Button to adjust setting on main window top right."""

    def __init__(self, window_main: QtWidgets.QMainWindow):
        super().__init__(window_main.ui.top_right_frame)
        self.setObjectName("settings_button")
        self.setFixedSize(38, 38)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.setStyleSheet(
            """
            QToolButton::menu-indicator { image: none; }
            """
        )
        self.setIcon(get_icon("settings.png"))
        self.setIconSize(QtCore.QSize(28, 28))
        self.setPopupMode(QtWidgets.QToolButton.InstantPopup)

        if window_main.system_info.platform == Platform.MACOS:
            self.move(0, 20)

        menu = SettingsMenu(self, window_main)
        window_main.settings_menu = menu
        self.setMenu(menu)
