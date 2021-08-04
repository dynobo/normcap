"""Create system tray and its menu."""

from PySide2 import QtCore, QtWidgets

from normcap import __version__
from normcap.logger import logger
from normcap.utils import get_icon


class Communicate(QtCore.QObject):
    """TrayMenus' communication bus."""

    on_capture = QtCore.Signal()
    on_exit = QtCore.Signal()


class SystemTray(QtWidgets.QSystemTrayIcon):
    """System tray icon with menu."""

    def __init__(self, parent: QtCore.QObject):
        logger.debug("Setting up tray icon")
        super().__init__(parent)
        self.com = Communicate()
        self.setIcon(get_icon("tray.png", "tool-magic-symbolic"))
        self._add_tray_menu()

    def _add_tray_menu(self):
        """Create menu for system tray."""
        menu = QtWidgets.QMenu()

        action = QtWidgets.QAction("Capture", menu)
        action.triggered.connect(self.com.on_capture.emit)  # pylint: disable=no-member
        menu.addAction(action)

        action = QtWidgets.QAction("Exit", menu)
        action.triggered.connect(self.com.on_exit.emit)  # pylint: disable=no-member
        menu.addAction(action)

        self.setContextMenu(menu)
