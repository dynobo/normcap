"""Create the settings button and its menu."""

from PySide2 import QtCore, QtGui, QtWidgets

from normcap.models import Platform


def open_url_and_hide(window, url):
    """Open url and quit or hide NormCap."""
    QtGui.QDesktopServices.openUrl(url)
    window.com.onQuitOrHide.emit()


# pylint: disable=too-many-statements
def create_menu(
    window: QtWidgets.QMainWindow, parent: QtWidgets.QWidget
) -> QtWidgets.QMenu:
    """Creat settings menu."""
    # pylint: disable=no-member  # action.triggered.connect is not resolved

    font = QtGui.QFont()
    font.setPixelSize(12)
    font.setBold(True)

    menu = QtWidgets.QMenu(parent)
    menu.setStyleSheet(
        f"""
        QMenu {{
            background-color: rgba(0,0,0,0.3);
            color: white;
        }}
        QMenu::separator {{
            background-color: rgba(255,255,255,0.2);
        }}
        QMenu::item {{
            padding: 4px 16px 4px 16px;
            background-color: transparent;
        }}
        QMenu::item:disabled {{
            color: {window.config.color};
        }}
        QMenu::item:selected {{
            background-color: rgba(150,150,150,0.5);
        }}
        QMenu::indicator {{
            position: relative;
            right: -5px;
        }}
        QMenu::indicator:unchecked {{
        }}
        QMenu::indicator:checked {{
        }}
        QMenu::left-arrow,
        QMenu::right-arrow {{
            margin: 5px;
        }}
        """
    )
    # Settings section

    action = QtWidgets.QAction("Settings:", menu)
    action.setEnabled(False)
    action.setFont(font)
    menu.addAction(action)

    action = QtWidgets.QAction("Show notifications", menu)
    action.setCheckable(True)
    action.setChecked(window.config.notifications)
    action.triggered.connect(lambda check: window.set_config("notifications", check))
    menu.addAction(action)

    action = QtWidgets.QAction("Keep in system tray", menu)
    action.setCheckable(True)
    action.setChecked(window.config.tray)
    action.triggered.connect(lambda check: window.set_config("tray", check))
    menu.addAction(action)

    action = QtWidgets.QAction("Check for updates", menu)
    action.setCheckable(True)
    action.setChecked(window.config.updates)
    action.triggered.connect(lambda check: window.set_config("updates", check))
    menu.addAction(action)

    menu.addSeparator()

    # Mode section

    action = QtWidgets.QAction("Capture mode:", menu)
    action.setEnabled(False)
    action.setFont(font)
    menu.addAction(action)

    mode_group = QtWidgets.QActionGroup(menu)
    mode_group.setExclusive(True)
    action = QtWidgets.QAction("parse", menu)
    action.setCheckable(True)
    action.triggered.connect(
        lambda check=True, mode="parse": window.set_config("mode", mode)
    )
    action.setChecked(window.config.mode == "parse")
    mode_group.addAction(action)
    menu.addAction(action)

    action = QtWidgets.QAction("raw", menu)
    action.setCheckable(True)
    action.triggered.connect(
        lambda check=True, mode="raw": window.set_config("mode", mode)
    )
    action.setChecked(window.config.mode == "raw")
    mode_group.addAction(action)
    menu.addAction(action)

    menu.addSeparator()

    # Language section

    action = QtWidgets.QAction("Languages:", menu)
    action.setEnabled(False)
    action.setFont(font)
    menu.addAction(action)

    for language in window.system_info.tesseract_languages:
        action = QtWidgets.QAction(language, menu)
        action.setCheckable(True)
        action.triggered.connect(
            lambda check=True, language=language: window.set_config(
                "languages", language
            )
        )
        action.setChecked(language in window.config.languages)
        menu.addAction(action)

    menu.addSeparator()

    # Final section
    action = QtWidgets.QAction("Application:", menu)
    action.setEnabled(False)
    action.setFont(font)
    menu.addAction(action)

    submenu = QtWidgets.QMenu(menu)
    submenu.setTitle("Website")

    action = QtWidgets.QAction("Source code", submenu)
    action.triggered.connect(
        lambda: open_url_and_hide(window, "https://github.com/dynobo/normcap")
    )
    submenu.addAction(action)

    action = QtWidgets.QAction("Releases", submenu)
    action.triggered.connect(
        lambda: open_url_and_hide(window, "https://github.com/dynobo/normcap/releases")
    )
    submenu.addAction(action)

    action = QtWidgets.QAction("FAQ", submenu)
    action.triggered.connect(
        lambda: open_url_and_hide(
            window, "https://github.com/dynobo/normcap/blob/main/FAQ.md"
        )
    )
    submenu.addAction(action)

    action = QtWidgets.QAction("Report a problem", submenu)
    action.triggered.connect(
        lambda: open_url_and_hide(window, "https://github.com/dynobo/normcap/issues")
    )
    submenu.addAction(action)

    menu.addMenu(submenu)

    action = QtWidgets.QAction("Exit", menu)
    action.triggered.connect(window.com.onQuitOrHide.emit)
    menu.addAction(action)

    return menu


def create_button(window: QtWidgets.QMainWindow) -> QtWidgets.QToolButton:
    """Creat settings button."""

    button = QtWidgets.QToolButton(window.ui.top_right_frame)
    button.setFixedSize(38, 38)
    button.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)

    # Move Button down on macOS as workaround for not being
    # visible behind the menu bar
    if window.system_info.platform == Platform.MACOS:
        button.move(0, 20)

    button.setIcon(window.get_icon("settings.png"))
    button.setIconSize(QtCore.QSize(24, 24))
    button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
    button.setCursor(QtCore.Qt.ArrowCursor)

    return button


def create_settings_button(window: QtWidgets.QMainWindow) -> QtWidgets.QToolButton:
    """Combine settings menu and button"""

    button = create_button(window)
    window.settings_menu = create_menu(window, button)

    button.setMenu(window.settings_menu)

    return button
