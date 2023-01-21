"""Find new version on github or pypi."""
import logging
import ssl
from urllib.request import urlopen

import certifi
from PySide6 import QtCore

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    """TrayMenus' communication bus."""

    on_download_finished = QtCore.Signal(bytes, str)  # response, url
    on_download_failed = QtCore.Signal(str, str)  # msg, url


class Worker(QtCore.QRunnable):
    def __init__(self, url: str) -> None:
        super().__init__()
        self.url = url
        self.com = Communicate()

    @QtCore.Slot()
    def run(self) -> None:
        try:
            context = ssl.create_default_context(cafile=certifi.where())
            with urlopen(self.url, context=context) as response:  # nosec B310
                raw_data = response.read()
        except Exception as e:
            msg = f"Exception '{e}' during download of '{self.url}'"
            logger.error(msg)
            self.com.on_download_failed.emit(msg, self.url)
        else:
            self.com.on_download_finished.emit(raw_data, self.url)


class Downloader(QtCore.QObject):
    """Download content using QNetworkAccessManager.

    It is async (provides signal) and avoids an issue on macOS, where the import
    of urllib.request fails with 'no module named _scproxy' in the packaged version.
    """

    def __init__(self) -> None:
        super().__init__()
        self.com = Communicate()
        self.threadpool = QtCore.QThreadPool()

    def get(self, url: str) -> None:
        """Start downloading url. Emits signal, when done."""
        logger.debug("Download %s", url)
        worker = Worker(url=url)
        worker.com.on_download_finished.connect(self.com.on_download_finished)
        worker.com.on_download_failed.connect(self.com.on_download_failed)
        self.threadpool.start(worker)
