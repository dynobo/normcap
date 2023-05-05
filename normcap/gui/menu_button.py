"""Create the settings button and its menu."""

from typing import Any, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from normcap import __version__
from normcap.gui.constants import MESSAGE_LANGUAGES, URLS

_MENU_STYLE = """
QMenu {
    background-color: rgba(0,0,0,0.8);
    color: white;
}
QMenu::separator {
    background-color: rgba(255,255,255,0.2);
    height: 1px;
    margin-top: 5px;
}
QMenu::scroller {
    background: qlineargradient(
        x1:1, y1:0, x2:1, y2:1,
        stop:0 rgba(0,0,0,0),
        stop:0.5 rgba(150,150,150,0.1),
        stop:1 rgba(0,0,0,0)
    )
}
QMenu::item {
    padding: 3px 16px 3px 16px;
    background-color: transparent;
    right: 10px;
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
QToolButton::hover {
    background: qradialgradient(
        cx: 0.5, cy: 0.5,
        fx: 0.5, fy: 0.5,
        radius: 0.55,
        stop: 0 rgba(0,0,0,0) stop: 0.25 rgba(255,255,255,120) stop: 0.95 rgba(0,0,0,0)
    );
}
QToolButton::menu-indicator { image: none; }
"""

# TODO: Add translations
# https://doc.qt.io/qtforpython-6/tutorials/basictutorial/translations.html


class Communicate(QtCore.QObject):
    """SettingsMenu' communication bus."""

    on_open_url = QtCore.Signal(str)
    on_close_in_settings = QtCore.Signal(str)
    on_manage_languages = QtCore.Signal()
    on_setting_change = QtCore.Signal(str)


class MenuButton(QtWidgets.QToolButton):
    """Button to adjust setting on main window top right."""

    title_font = QtGui.QFont(QtGui.QFont().family(), pointSize=10, weight=600)

    def __init__(
        self,
        settings: QtCore.QSettings,
        installed_languages: list[str],
        language_manager: bool = False,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.languages = installed_languages
        self.setObjectName("settings_icon")
        self.settings = settings
        self.has_language_manager = language_manager

        self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
        self.setFixedSize(44, 44)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)

        self.setIcon(QtGui.QIcon(":settings"))
        self.setIconSize(QtCore.QSize(32, 32))
        self.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.setAutoRaise(True)

        self.message_box = QtWidgets.QMessageBox()
        self.message_box.setIconPixmap(QtGui.QIcon(":normcap").pixmap(48, 48))
        # Necessary on wayland for main window to regain focus:
        self.message_box.setWindowFlags(QtCore.Qt.WindowType.Popup)

        self.setMenu(self._create_menu())

        self.setStyleSheet(_BUTTON_STYLE)
        self.com = Communicate()

    def _create_menu(self) -> QtWidgets.QMenu:
        menu = QtWidgets.QMenu(self)
        menu.setObjectName("settings_menu")
        menu.setStyleSheet(
            _MENU_STYLE.replace("$COLOR", str(self.settings.value("color")))
        )
        menu.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        menu.triggered.connect(self.on_item_click)
        menu.aboutToShow.connect(self.populate_menu_entries)
        return menu

    @QtCore.Slot(list)
    def on_languages_changed(self, installed_languages: list[str]) -> None:
        self.languages = installed_languages

    @QtCore.Slot(QtGui.QAction)
    def on_item_click(self, action: QtGui.QAction) -> None:
        action_name = action.objectName()
        group = action.actionGroup()
        group_name = group.objectName() if group else None
        value: Optional[Any] = None
        setting = None

        if action_name == "close":
            self.com.on_close_in_settings.emit("Clicked close in settings")
            return

        if action_name == "show_help_languages":
            self.message_box.setText(MESSAGE_LANGUAGES)
            self.message_box.exec_()
            return

        if action_name == "manage_languages":
            self.com.on_manage_languages.emit()
            return

        if group_name == "website_group" or action_name.startswith("file:/"):
            self.com.on_open_url.emit(action_name)
            return

        if group_name == "settings_group":
            setting = action_name
            value = action.isChecked()
        elif group_name == "mode_group":
            setting = "mode"
            value = action_name
        elif group_name == "language_group":
            setting = "language"
            languages = [a.objectName() for a in group.actions() if a.isChecked()]
            if not languages:
                languages = [action_name]
                action.setChecked(True)
            value = languages

        if None not in (setting, value):
            self.settings.setValue(str(setting), value)
            self.com.on_setting_change.emit(str(setting))

    @QtCore.Slot()
    def populate_menu_entries(self) -> None:
        menu = self.menu()
        menu.clear()

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

    def _add_title(
        self,
        menu: QtWidgets.QMenu,
        text: str,
        action_parent: Optional[QtGui.QAction] = None,
    ) -> None:
        action = QtGui.QAction(text, action_parent or menu)
        action.setEnabled(False)
        action.setFont(self.title_font)
        menu.addAction(action)

    def _add_settings_section(
        self, menu: QtWidgets.QMenu
    ) -> None:  # sourcery skip: class-extract-method
        settings_group = QtGui.QActionGroup(menu)
        settings_group.setObjectName("settings_group")
        settings_group.setExclusive(False)

        action = QtGui.QAction("Show notification", settings_group)
        action.setObjectName("notification")
        action.setCheckable(True)
        action.setChecked(bool(self.settings.value("notification", type=bool)))
        menu.addAction(action)

        action = QtGui.QAction("Keep in system tray", settings_group)
        action.setObjectName("tray")
        action.setCheckable(True)
        action.setChecked(bool(self.settings.value("tray", type=bool)))
        menu.addAction(action)

        action = QtGui.QAction("Check for update", settings_group)
        action.setObjectName("update")
        action.setCheckable(True)
        action.setChecked(bool(self.settings.value("update", type=bool)))
        menu.addAction(action)

    def _add_mode_section(self, menu: QtWidgets.QMenu) -> None:
        mode_group = QtGui.QActionGroup(menu)
        mode_group.setObjectName("mode_group")
        mode_group.setExclusive(True)

        action = QtGui.QAction("parse", mode_group)
        action.setObjectName("parse")
        action.setCheckable(True)
        action.setChecked(self.settings.value("mode") == "parse")
        menu.addAction(action)

        action = QtGui.QAction("raw", mode_group)
        action.setObjectName("raw")
        action.setCheckable(True)
        action.setChecked(self.settings.value("mode") == "raw")
        menu.addAction(action)

    def _add_languages_section(self, menu: QtWidgets.QMenu) -> None:
        languages = self.languages
        overflow_languages_count = 7
        if len(languages) <= overflow_languages_count:
            language_menu = menu
        else:
            language_menu = QtWidgets.QMenu("select", menu)
            language_menu.setObjectName("language_menu")
            menu.addMenu(language_menu)

        language_group = QtGui.QActionGroup(language_menu)
        language_group.setObjectName("language_group")
        language_group.setExclusive(False)
        for language in languages:
            action = QtGui.QAction(language, language_group)
            action.setObjectName(language)
            action.setCheckable(True)
            action.setChecked(language in str(self.settings.value("language")))
            language_menu.addAction(action)

        if self.has_language_manager:
            action = QtGui.QAction("add/remove...", menu)
            action.setObjectName("manage_languages")
        else:
            action = QtGui.QAction("... need more?", menu)
            action.setObjectName("show_help_languages")

        menu.addAction(action)

    def _add_application_section(self, menu: QtWidgets.QMenu) -> None:
        submenu = QtWidgets.QMenu(menu)
        submenu.setObjectName("settings_menu_website")
        submenu.setTitle("About")

        about_group = QtGui.QActionGroup(menu)
        about_group.setObjectName("website_group")

        self._add_title(submenu, f"Normcap v{__version__}", about_group)

        action = QtGui.QAction("Website", about_group)
        action.setObjectName(URLS.website)
        submenu.addAction(action)

        action = QtGui.QAction("FAQs", about_group)
        action.setObjectName(URLS.faqs)
        submenu.addAction(action)

        action = QtGui.QAction("Source code", about_group)
        action.setObjectName(URLS.github)
        submenu.addAction(action)

        action = QtGui.QAction("Releases", about_group)
        action.setObjectName(URLS.releases)
        submenu.addAction(action)

        action = QtGui.QAction("Report a problem", about_group)
        action.setObjectName(URLS.issues)
        submenu.addAction(action)

        action = QtGui.QAction("Buy me a coffee", about_group)
        action.setObjectName(URLS.buymeacoffee)
        submenu.addAction(action)

        menu.addMenu(submenu)

        action = QtGui.QAction("Close", menu)
        action.setObjectName("close")
        menu.addAction(action)
