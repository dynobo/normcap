"""Download any file from url asynchronously."""

import logging

from PySide6 import QtCore

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    """TrayMenus' communication bus."""

    on_download_finished = QtCore.Signal(bytes, str)  # response, url
    on_download_failed = QtCore.Signal(str, str)  # msg, url


class Worker(QtCore.QRunnable):
    def __init__(self, url: str, timeout: int = 30) -> None:
        super().__init__()
        self.url = url
        self.timeout = timeout
        self.com = Communicate()

    @staticmethod
    def _raise_on_non_safe_urls(url: str) -> None:
        if not url.startswith("http"):
            raise ValueError(f"Downloading from {url[:9]}... is not allowed.")

    @QtCore.Slot()
    def run(self) -> None:
        try:
            import ssl
            from urllib.request import urlopen

            context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
            context.load_default_certs()
            if not context.get_ca_certs():
                context = ssl._create_unverified_context()  # noqa: S323
                logger.debug("Fallback to ssl without verification")

            self._raise_on_non_safe_urls(url=self.url)

            with urlopen(  # noqa: S310
                self.url, context=context, timeout=self.timeout
            ) as response:
                raw_data = response.read()
        except Exception as e:
            msg = f"Exception '{e}' during download of '{self.url}'"
            logger.exception(msg)
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

    def get(self, url: str, timeout: int = 30) -> None:
        """Start downloading url. Emits signal, when done."""
        logger.debug("Download %s", url)
        worker = Worker(url=url, timeout=timeout)
        worker.com.on_download_finished.connect(self.com.on_download_finished)
        worker.com.on_download_failed.connect(self.com.on_download_failed)
        self.threadpool.start(worker)
