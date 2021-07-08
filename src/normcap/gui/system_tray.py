"""Create system tray and its menu."""

import sys

from PySide2 import QtGui, QtWidgets

from normcap import __version__
from normcap.logger import logger


def create_tray_menu(window: QtWidgets.QMainWindow) -> QtWidgets.QMenu:
    """Create menu for system tray."""
    # pylint: disable=no-member  # action.triggered.connect is not resolved

    font = QtGui.QFont()
    font.setPixelSize(12)
    font.setBold(True)

    menu = QtWidgets.QMenu()

    action = QtWidgets.QAction("Capture", menu)
    action.triggered.connect(window.show_windows)
    menu.addAction(action)

    action = QtWidgets.QAction("Exit", menu)
    action.triggered.connect(sys.exit)
    menu.addAction(action)

    menu.addSeparator()

    action = QtWidgets.QAction(f"NormCap {__version__}", menu)
    action.setEnabled(False)
    action.setFont(font)
    menu.addAction(action)

    action = QtWidgets.QAction("- Website", menu)
    action.triggered.connect(
        lambda: QtGui.QDesktopServices.openUrl("https://github.com/dynobo/normcap")
    )
    menu.addAction(action)

    action = QtWidgets.QAction("- Releases", menu)
    action.triggered.connect(
        lambda: QtGui.QDesktopServices.openUrl(
            "https://github.com/dynobo/normcap/releases"
        )
    )
    menu.addAction(action)

    action = QtWidgets.QAction("- FAQ", menu)
    action.triggered.connect(
        lambda: QtGui.QDesktopServices.openUrl(
            "https://github.com/dynobo/normcap/blob/main/FAQ.md"
        )
    )
    menu.addAction(action)

    action = QtWidgets.QAction("- Report a Problem", menu)
    action.triggered.connect(
        lambda: QtGui.QDesktopServices.openUrl(
            "https://github.com/dynobo/normcap/issues"
        )
    )
    menu.addAction(action)

    return menu


def create_system_tray(window: QtWidgets.QMainWindow) -> QtWidgets.QSystemTrayIcon:
    """Setting up tray icon."""
    logger.debug("Setting up tray icon")
    menu = create_tray_menu(window)
    tray = QtWidgets.QSystemTrayIcon()
    tray_icon = window.get_icon("tray.png", "tool-magic-symbolic")
    tray.setIcon(tray_icon)
    tray.setContextMenu(menu)
    return tray
