"""Create the settings button and its menu."""

import sys
from typing import Any, Optional, Union

from PySide6 import QtCore, QtGui, QtWidgets

from normcap import __version__
from normcap.gui.constants import URLS
from normcap.gui.localization import _

_MENU_STYLE = """
QMenu {
    background-color: rgba(0,0,0,0.8);
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
    color: white;
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
QToolTip {
    background-color: rgba(50,50,50,1);
    color: white;
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


class Communicate(QtCore.QObject):
    """SettingsMenu' communication bus."""

    on_open_url = QtCore.Signal(str)
    on_close_in_settings = QtCore.Signal(str)
    on_manage_languages = QtCore.Signal()
    on_setting_change = QtCore.Signal(str)
    on_show_introduction = QtCore.Signal()


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
        super().__init__(parent=parent)
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

        self.setMenu(self._create_menu())

        self.setStyleSheet(_BUTTON_STYLE)
        self.com = Communicate()

    def _create_menu(self) -> QtWidgets.QMenu:
        menu = QtWidgets.QMenu(self)
        menu.setParent(self)
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

    def _show_message_box(self, text: str) -> None:
        message_box = QtWidgets.QMessageBox(parent=self)
        message_box.setIconPixmap(QtGui.QIcon(":normcap").pixmap(48, 48))
        # Necessary at least on Wayland:
        # - Makes the message box close when the window is clicked
        # - Avoids the state where the message box has focus but is behind the window
        message_box.setWindowFlags(QtCore.Qt.WindowType.Popup)
        message_box.setText(text)
        message_box.exec()

    @QtCore.Slot(QtGui.QAction)
    def on_item_click(self, action: QtGui.QAction) -> None:
        # TODO: Reduce Cyclomatic Complexity
        action_name = action.objectName()
        group = action.actionGroup()
        group_name = group.objectName() if group else None
        value: Optional[Any] = None

        # Menu items which trigger actions

        if action_name == "close":
            self.com.on_close_in_settings.emit("Clicked close in settings")
            return

        if action_name == "show_help_languages":
            # L10N: Message box shown in Python package when trying to install language
            self._show_message_box(
                text=_(
                    "This installation of NormCap uses the Tesseract binary installed "
                    "on your system. To install additional languages, please refer to "
                    "the documentation of that Tesseract installation."
                )
            )
            return

        if action_name == "manage_languages":
            self.com.on_manage_languages.emit()
            return

        if action_name == "show_introduction":
            self.com.on_show_introduction.emit()
            return

        if action_name.startswith(("file:/", "https:/")):
            self.com.on_open_url.emit(action_name)
            return

        # Menu items which change settings

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

        self.settings.setValue(str(setting), value)
        self.com.on_setting_change.emit(str(setting))

    @QtCore.Slot()
    def populate_menu_entries(self) -> None:
        menu = self.menu()
        menu.clear()
        menu.setToolTipsVisible(True)

        # L10N: Section title in Main Menu
        self._add_title(menu, _("Settings"))
        self._add_settings_section(menu)
        menu.addSeparator()
        # L10N: Section title in Main Menu
        self._add_title(menu, _("Capture mode"))
        self._add_mode_section(menu)
        menu.addSeparator()
        # L10N: Section title in Main Menu
        self._add_title(menu, _("Languages"))
        self._add_languages_section(menu)
        menu.addSeparator()
        # L10N: Section title in Main Menu
        self._add_title(menu, _("Application"))
        self._add_application_section(menu)

    def _add_title(
        self,
        menu: QtWidgets.QMenu,
        text: str,
        action_parent: Union[QtGui.QAction, QtGui.QActionGroup, None] = None,
    ) -> None:
        action = QtGui.QAction(text, action_parent or menu)
        action.setEnabled(False)
        action.setFont(self.title_font)
        menu.addAction(action)

    def _add_settings_section(self, menu: QtWidgets.QMenu) -> None:
        settings_group = QtGui.QActionGroup(menu)
        settings_group.setObjectName("settings_group")
        settings_group.setExclusive(False)

        # L10N: Entry in main menu's 'setting' section
        action = QtGui.QAction(_("Show notification"), settings_group)
        action.setObjectName("notification")
        action.setCheckable(True)
        action.setChecked(bool(self.settings.value("notification", type=bool)))
        # L10N: Tooltip of main menu's "Show notification" entry. Use <56 chars p. line.
        notification_tooltip = _(
            "Show status information via your system's desktop\nnotification center."
        )
        if sys.platform in {"darwin", "win32"}:
            notification_tooltip += (
                # L10N: Extension "Show notification"-Tooltip on macOS and Windows.
                f"\n({_('Click on the notification to open the result')})"
            )
        action.setToolTip(notification_tooltip)
        menu.addAction(action)

        # L10N: Entry in main menu's 'setting' section
        action = QtGui.QAction(_("Keep in system tray"), settings_group)
        action.setObjectName("tray")
        action.setCheckable(True)
        action.setChecked(bool(self.settings.value("tray", type=bool)))
        # L10N: Tooltip of main menu's "Keep in tray" entry. Use <56 chars p. line.
        action.setToolTip(
            _(
                "Keep NormCap running in the background. Another\n"
                "capture can be triggered via the tray icon."
            )
        )
        menu.addAction(action)

        # L10N: Entry in main menu's 'setting' section
        action = QtGui.QAction(_("Check for update"), settings_group)
        action.setObjectName("update")
        action.setCheckable(True)
        action.setChecked(bool(self.settings.value("update", type=bool)))
        # L10N: Tooltip of main menu's "Update" entry. Use <56 chars p. line.
        action.setToolTip(
            _(
                "Frequently fetch NormCap's releases online and display\n"
                "a message if a new version is available."
            )
        )
        menu.addAction(action)

    def _add_mode_section(self, menu: QtWidgets.QMenu) -> None:
        mode_group = QtGui.QActionGroup(menu)
        mode_group.setObjectName("mode_group")
        mode_group.setExclusive(True)

        # L10N: Entry in main menu's 'Capture mode' section
        action = QtGui.QAction(_("parse"), mode_group)
        action.setObjectName("parse")
        action.setCheckable(True)
        action.setChecked(self.settings.value("mode") == "parse")
        # L10N: Tooltip of main menu's 'parse' entry. Use <56 chars p. line.
        action.setToolTip(
            _(
                "Tries to determine the text's type (e.g. line,\n"
                "paragraph, URL, email) and formats the output\n"
                "accordingly.\n"
                "If the result is unexpected, try 'raw' mode instead."
            )
        )
        menu.addAction(action)

        # L10N: Entry in main menu's 'Capture mode' section
        action = QtGui.QAction(_("raw"), mode_group)
        action.setObjectName("raw")
        action.setCheckable(True)
        action.setChecked(self.settings.value("mode") == "raw")
        # L10N: Tooltip of main menu's 'raw' entry. Use <56 chars p. line.
        action.setToolTip(
            _(
                "Returns the text exactly as detected by the Optical\n"
                "Character Recognition Software."
            )
        )
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
            # L10N: Entry in main menu's 'Languages' section. Shown in prebuilt package.
            action = QtGui.QAction(_("add/remove..."), menu)
            action.setObjectName("manage_languages")
        else:
            # L10N: Entry in main menu's 'Languages' section. Shown in Python package.
            action = QtGui.QAction(_("... need more?"), menu)
            action.setObjectName("show_help_languages")

        menu.addAction(action)

    def _add_application_section(self, menu: QtWidgets.QMenu) -> None:
        submenu = QtWidgets.QMenu(menu)
        submenu.setObjectName("settings_menu_website")
        # L10N: Entry in main menu's 'Application' section.
        submenu.setTitle(_("About"))

        about_group = QtGui.QActionGroup(menu)
        about_group.setObjectName("website_group")

        self._add_title(submenu, f"Normcap v{__version__}", about_group)

        # L10N: Entry in main menu's 'Application' section.
        action = QtGui.QAction(_("Introduction"), menu)
        action.setObjectName("show_introduction")
        submenu.addAction(action)

        # L10N: Entry in main menu's 'Application' section.
        action = QtGui.QAction(_("Website"), about_group)
        action.setObjectName(URLS.website)
        submenu.addAction(action)

        # L10N: Entry in main menu's 'Application' section.
        action = QtGui.QAction(_("FAQs"), about_group)
        action.setObjectName(URLS.faqs)
        submenu.addAction(action)

        # L10N: Entry in main menu's 'Application' section.
        action = QtGui.QAction(_("Source code"), about_group)
        action.setObjectName(URLS.github)
        submenu.addAction(action)

        # L10N: Entry in main menu's 'Application' section.
        action = QtGui.QAction(_("Releases"), about_group)
        action.setObjectName(URLS.releases)
        submenu.addAction(action)

        # L10N: Entry in main menu's 'Application' section.
        action = QtGui.QAction(_("Report a problem"), about_group)
        action.setObjectName(URLS.issues)
        submenu.addAction(action)

        # L10N: Entry in main menu's 'Application' section.
        action = QtGui.QAction(_("Donate for coffee"), about_group)
        action.setObjectName(URLS.buymeacoffee)
        submenu.addAction(action)

        menu.addMenu(submenu)

        # L10N: Entry in main menu's 'Application' section.
        action = QtGui.QAction(_("Close"), menu)
        action.setObjectName("close")
        # L10N: Tooltip of main menu's 'close' entry. Use <56 chars p. line.
        action.setToolTip(_("Exit NormCap, or minimize to system tray (if enabled)."))
        menu.addAction(action)
