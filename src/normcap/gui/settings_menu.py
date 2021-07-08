"""Create the settings button and its menu."""

from PySide2 import QtCore, QtGui, QtWidgets


# pylint: disable=too-many-statements
def create_menu(window: QtWidgets.QMainWindow) -> QtWidgets.QMenu:
    """Creat settings menu."""
    # pylint: disable=no-member  # action.triggered.connect is not resolved

    font = QtGui.QFont()
    font.setPixelSize(12)
    font.setBold(True)

    menu = QtWidgets.QMenu()

    # Settings section

    action = QtWidgets.QAction("Settings:", menu)
    action.setEnabled(False)
    action.setFont(font)
    menu.addAction(action)

    action = QtWidgets.QAction("Show Notifications", menu)
    action.setCheckable(True)
    action.setChecked(window.config.notifications)
    action.triggered.connect(lambda check: window.set_config("notifications", check))
    menu.addAction(action)

    action = QtWidgets.QAction("Keep in System Tray", menu)
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

    action = QtWidgets.QAction("Mode:", menu)
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

    action = QtWidgets.QAction("Exit", menu)
    action.triggered.connect(window.com.onQuitOrHide.emit)
    menu.addAction(action)

    return menu


def create_button(window: QtWidgets.QMainWindow) -> QtWidgets.QToolButton:
    """Creat settings button."""

    button = QtWidgets.QToolButton(window.ui.top_right_frame)
    button.setFixedSize(32, 32)
    button.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
    button.setStyleSheet(
        """
        QToolButton::menu-indicator {
            image: none;
        }
        QToolButton {
            text-align: center;
            color: red;
        }
        """
    )

    font = QtGui.QFont()
    font.setPixelSize(32)
    font.setBold(True)
    button.setFont(font)
    button.setText("⚙")

    button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
    button.setCursor(QtCore.Qt.ArrowCursor)
    return button


def create_settings_button(window: QtWidgets.QMainWindow) -> QtWidgets.QToolButton:
    """Combine settings menu and button"""

    window.settings_menu = create_menu(window)

    button = create_button(window)
    button.setMenu(window.settings_menu)

    return button
