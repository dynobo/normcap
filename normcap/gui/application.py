"""Start main application logic."""

import logging
from typing import Any

from PySide6 import QtCore, QtNetwork, QtWidgets

from normcap import __version__
from normcap.gui.models import Rect, Seconds
from normcap.gui.tray import SystemTray

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    """TrayMenus' communication bus."""

    on_exit_application = QtCore.Signal(float)
    on_copied_to_clipboard = QtCore.Signal()
    on_region_selected = QtCore.Signal(Rect, int)
    on_languages_changed = QtCore.Signal(list)
    on_action_finished = QtCore.Signal()


class Timers:
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        self.delayed_exit = QtCore.QTimer(parent=parent, singleShot=True)


class NormcapApp(QtWidgets.QApplication):
    # Used for singleton:
    _socket_name = f"v{__version__}-normcap"
    _socket_out: QtNetwork.QLocalSocket | None = None
    _socket_in: QtNetwork.QLocalSocket | None = None
    _socket_server: QtNetwork.QLocalServer | None = None

    def __init__(self, args: dict[str, Any]) -> None:
        super().__init__()
        self.setQuitOnLastWindowClosed(False)
        self.com = Communicate(parent=self)
        self.timers = Timers(parent=self)
        self.timers.delayed_exit.timeout.connect(self.quit)

        self.com.on_exit_application.connect(self._exit_application)

        # Ensure that only a single instance of NormCap is running.
        if self._other_instance_is_running():
            self.com.on_exit_application.emit(0)
            return

        self._create_socket_server()

        self.tray = SystemTray(self, args)
        self.tray.show()

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

        self.tray._show_windows(delay_screenshot=True)

    @QtCore.Slot(bool)
    def _exit_application(self, delay: Seconds) -> None:
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
