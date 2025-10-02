import atexit
import logging

from PySide6 import QtCore, QtNetwork

from normcap import __version__

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    """Application's communication bus."""

    on_capture_message = QtCore.Signal()
    on_other_instance_running = QtCore.Signal()


class SocketServer(QtCore.QObject):
    _name = f"v{__version__}-normcap"
    _out: QtNetwork.QLocalSocket | None = None
    _in: QtNetwork.QLocalSocket | None = None
    _server: QtNetwork.QLocalServer | None = None
    is_first_instance: bool

    def __init__(self) -> None:
        super().__init__()
        self.com = Communicate()

        self._out = self._connect_to_other_instance()
        if self._out:
            # Send message to other instance
            logger.debug("Another instance is already running. Sending capture signal.")
            self._out.write(b"capture")
            self._out.waitForBytesWritten(1000)
            self.is_first_instance = False
        else:
            # Start server
            self._create_socket_server()
            self.is_first_instance = True
            atexit.register(self.close)

    def _connect_to_other_instance(self) -> QtNetwork.QLocalSocket | None:
        """Test if connection to another NormCap instance socket can be established."""
        self._out = QtNetwork.QLocalSocket(self)
        self._out.connectToServer(self._name)
        if not self._out.waitForConnected():
            # Couldn't connect, cleaning up out
            self._out.close()
            self._out = None

        return self._out

    def _create_socket_server(self) -> None:
        """Open socket server to listen for other NormCap instances."""
        QtNetwork.QLocalServer().removeServer(self._name)
        self._server = QtNetwork.QLocalServer(self)
        self._server.newConnection.connect(self._on_socket_connect)
        self._server.listen(self._name)
        logger.debug("Listen on local socket %s.", self._server.serverName())

    @QtCore.Slot()
    def _on_socket_connect(self) -> None:
        """Open incoming socket to listen for messages from other NormCap instances."""
        if not self._server:
            return
        self._in = self._server.nextPendingConnection()
        if self._in:
            logger.debug("Connect to incoming socket.")
            self._in.readyRead.connect(self._on_socket_ready_read)

    @QtCore.Slot()
    def _on_socket_ready_read(self) -> None:
        """Process messages received from other NormCap instances."""
        if not self._in:
            return

        message = self._in.readAll().data().decode("utf-8", errors="ignore")
        logger.info("Received socket message '%s'", message)

        if message == "capture":
            self.com.on_capture_message.emit()

    def close(self) -> None:
        if self._out:
            self._out.close()
            self._out = None

        if self._server:
            self._server.close()
            self._server.removeServer(self._name)
            self._server = None
