"""Create system tray and its menu."""
import logging

from PySide6 import QtCore, QtGui, QtWidgets

from normcap import __version__
from normcap.gui.utils import get_icon

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    """TrayMenus' communication bus."""

    on_capture = QtCore.Signal()
    on_exit = QtCore.Signal()


class SystemTray(QtWidgets.QSystemTrayIcon):
    """System tray icon with menu."""

    def __init__(self, parent: QtCore.QObject):
        logger.debug("Set up tray icon")
        super().__init__(parent)
        self.com = Communicate()
        self.setIcon(get_icon("tray.png", "tool-magic-symbolic"))
        self._add_tray_menu()

    def _add_tray_menu(self):
        """Create menu for system tray."""
        menu = QtWidgets.QMenu()

        action = QtGui.QAction("Capture", menu)
        action.triggered.connect(self.com.on_capture.emit)  # pylint: disable=no-member
        menu.addAction(action)

        action = QtGui.QAction("Exit", menu)
        action.triggered.connect(self.com.on_exit.emit)  # pylint: disable=no-member
        menu.addAction(action)

        self.setContextMenu(menu)
