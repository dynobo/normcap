"""Create the settings button and its menu."""

from typing import Any

from PySide2 import QtCore, QtGui, QtWidgets

from normcap.models import URLS
from normcap.utils import get_icon

_MENU_STYLE = """
        QMenu {
            background-color: rgba(0,0,0,0.8);
            color: white;
            right: 20px;
            margin-right: 10px;
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
            right: -5px;
        }
        QMenu::left-arrow,
        QMenu::right-arrow  {
            right: 15px;
        }
    """

_BUTTON_STYLE = """
        QToolButton { border:0px; }
        QToolButton::menu-indicator { image: none; }
    """


class Communicate(QtCore.QObject):
    """SettingsMenu' communication bus."""

    on_setting_changed = QtCore.Signal(tuple)
    on_open_url = QtCore.Signal(str)
    on_quit_or_hide = QtCore.Signal()


class SettingsMenu(QtWidgets.QToolButton):
    """Button to adjust setting on main window top right."""

    def __init__(self, window_main: QtWidgets.QMainWindow):
        super().__init__(window_main.frame)
        self.setObjectName("settings_icon")
        self.settings = window_main.settings
        self.system_info = window_main.system_info

        self.setCursor(QtCore.Qt.ArrowCursor)
        self.setFixedSize(38, 38)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.setStyleSheet(_BUTTON_STYLE)

        self.setIcon(get_icon("settings.png"))
        self.setIconSize(QtCore.QSize(28, 28))
        self.setPopupMode(QtWidgets.QToolButton.InstantPopup)

        self.title_font = QtGui.QFont(QtGui.QFont().family(), 10, QtGui.QFont.Bold)
        self._add_menu()

        self.com = Communicate()

    def _add_menu(self):
        menu = QtWidgets.QMenu(self)
        menu.setObjectName("settings_menu")
        menu.setStyleSheet(_MENU_STYLE.replace("$COLOR", self.settings.value("color")))
        menu.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

        self._add_title(menu, "Settings")
        self._add_settings_section(menu)
        menu.addSeparator()
        self._add_title(menu, "Capture mode")
        self._add_mode_section(menu)
        menu.addSeparator()
        self._add_title(menu, "Languages")
        self._add_languages_section(menu)
        menu.addSeparator()
        self._add_title(menu, "Application")
        self._add_application_section(menu)
        menu.triggered.connect(self._on_item_click)  # pylint: disable=no-member

        self.setMenu(menu)

    def _add_title(self, menu, title: str):
        action = QtWidgets.QAction(title, menu)
        action.setEnabled(False)
        action.setFont(self.title_font)
        menu.addAction(action)

    def _on_item_click(self, action: QtWidgets.QAction):
        group = action.actionGroup()
        group_name = group.objectName() if group else None
        value: Any = None
        if action.objectName() == "close":
            self.com.on_quit_or_hide.emit()
            return

        if group_name == "website_group":
            url = action.objectName()
            self.com.on_open_url.emit(url)
            return

        if group_name == "settings_group":
            setting = action.objectName()
            value = action.isChecked()
        elif group_name == "mode_group":
            setting = "mode"
            value = action.objectName()
        elif group_name == "language_group":
            setting = "language"
            value = tuple(a.objectName() for a in group.actions() if a.isChecked())
            if len(value) < 1:
                value = tuple(action.objectName())
                action.setChecked(True)
        self.com.on_setting_changed.emit((setting, value))

    def _add_settings_section(self, menu):
        settings_group = QtWidgets.QActionGroup(menu)
        settings_group.setObjectName("settings_group")
        settings_group.setExclusive(False)

        action = QtWidgets.QAction("Show notification", settings_group)
        action.setObjectName("notification")
        action.setCheckable(True)
        action.setChecked(bool(self.settings.value("notification", type=bool)))
        menu.addAction(action)

        action = QtWidgets.QAction("Keep in system tray", settings_group)
        action.setObjectName("tray")
        action.setCheckable(True)
        action.setChecked(bool(self.settings.value("tray", type=bool)))
        menu.addAction(action)

        action = QtWidgets.QAction("Check for update", settings_group)
        action.setObjectName("update")
        action.setCheckable(True)
        action.setChecked(bool(self.settings.value("update", type=bool)))
        menu.addAction(action)

    def _add_mode_section(self, menu):
        mode_group = QtWidgets.QActionGroup(menu)
        mode_group.setObjectName("mode_group")
        mode_group.setExclusive(True)

        action = QtWidgets.QAction("parse", mode_group)
        action.setObjectName("parse")
        action.setCheckable(True)
        action.setChecked(self.settings.value("mode") == "parse")
        menu.addAction(action)

        action = QtWidgets.QAction("raw", mode_group)
        action.setObjectName("raw")
        action.setCheckable(True)
        action.setChecked(self.settings.value("mode") == "raw")
        menu.addAction(action)

    def _add_languages_section(self, menu):
        language_group = QtWidgets.QActionGroup(menu)
        language_group.setObjectName("language_group")
        language_group.setExclusive(False)
        for language in self.system_info.tesseract_languages:
            action = QtWidgets.QAction(language, language_group)
            action.setObjectName(language)
            action.setCheckable(True)
            action.setChecked(language in self.settings.value("language"))
            menu.addAction(action)

    @staticmethod
    def _add_application_section(menu):
        submenu = QtWidgets.QMenu(menu)
        submenu.setObjectName("settings_menu_website")
        submenu.setTitle("Website")

        website_group = QtWidgets.QActionGroup(menu)
        website_group.setObjectName("website_group")

        action = QtWidgets.QAction("Source code", website_group)
        action.setObjectName(URLS.github)
        submenu.addAction(action)

        action = QtWidgets.QAction("Releases", website_group)
        action.setObjectName(URLS.releases)
        submenu.addAction(action)

        action = QtWidgets.QAction("FAQ", website_group)
        action.setObjectName(URLS.faqs)
        submenu.addAction(action)

        action = QtWidgets.QAction("Report a problem", website_group)
        action.setObjectName(URLS.issues)
        submenu.addAction(action)

        menu.addMenu(submenu)

        action = QtWidgets.QAction("Close", menu)
        action.setObjectName("close")
        menu.addAction(action)
