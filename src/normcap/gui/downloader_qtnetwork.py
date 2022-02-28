"""Find new version on github or pypi."""
import logging

from PySide6 import QtCore, QtNetwork

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    """TrayMenus' communication bus."""

    on_download_finished = QtCore.Signal(str)
    on_download_failed = QtCore.Signal()


class Downloader(QtCore.QObject):
    """Downloader using QNetworkAccessManager.

    It is async (provides signal) and avoids an issue on MacOS, where the import
    of urllib.request fails with 'no module named _scproxy' in the packaged version.
    """

    def __init__(self):
        super().__init__()
        self.com = Communicate()
        self.manager = QtNetwork.QNetworkAccessManager()
        self.manager.finished.connect(  # pylint: disable=no-member
            self._on_get_finished
        )

    def get(self, url: str):
        """Start downloading url. Emits signal, when done."""
        logger.debug("Download %s", url)
        request = QtNetwork.QNetworkRequest(QtCore.QUrl(url))
        request.setTransferTimeout(3000)
        self.manager.get(request)

    def _on_get_finished(self, reply):
        """Decode response and emit download finished signal."""
        er = reply.error()
        if er != QtNetwork.QNetworkReply.NoError:
            logger.error("Download failed due to %s: %s", er, reply.errorString())
            self.com.on_download_failed.emit()
            return

        raw_data = str(reply.readAll(), "utf-8")
        self.com.on_download_finished.emit(raw_data)
