"""Download any file from url asynchronously."""

import logging
from typing import Optional

from PySide6 import QtCore

from normcap.gui.localization import _

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    """TrayMenus' communication bus."""

    on_download_finished = QtCore.Signal(bytes, str)  # response, url
    on_download_failed = QtCore.Signal(str, str)  # msg, url


class Worker(QtCore.QRunnable):
    def __init__(self, url: str, timeout: float = 30) -> None:
        super().__init__()
        self.url = url
        self.timeout = timeout
        self.com = Communicate()

    @staticmethod
    def _raise_on_non_safe_urls(url: str) -> None:
        if not url.startswith("http"):
            raise ValueError("Downloading from unsafe url is not allowed.")

    @QtCore.Slot()
    def run(self) -> None:
        logger.debug("Run download worker")
        try:
            import ssl
            from urllib.request import urlopen

            context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
            context.load_default_certs()
            if not context.get_ca_certs():
                context = ssl._create_unverified_context()  # noqa: S323
                logger.debug("Fallback to ssl without verification")

            self._raise_on_non_safe_urls(url=self.url)

            logger.debug("Request data from %s", self.url)
            with urlopen(  # noqa: S310
                self.url, context=context, timeout=self.timeout
            ) as response:
                logger.debug(
                    "Received response with status %s",
                    getattr(response, "status", None),
                )
                raw_data = response.read()
        except Exception as exc:
            logger.exception("Could not download '%s'", self.url)
            # L10N: Generic error message when any download failed.
            msg = _("Download error.")
            msg += f"\n[URL: {self.url}, EXC: {exc}]"
            self.com.on_download_failed.emit(msg, self.url)
        else:
            self.com.on_download_finished.emit(raw_data, self.url)


class Downloader(QtCore.QObject):
    """Download content async using a threadpool and urllib.

    It is async (provides signal) and avoids an issue on macOS, where the import
    of urllib.request fails with 'no module named _scproxy' in the packaged version.
    """

    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent=parent)
        self.com = Communicate()
        self.threadpool = QtCore.QThreadPool()
        self.worker: Optional[Worker] = None

    def get(self, url: str, timeout: float = 30) -> None:
        """Start downloading url. Emits failed or finished signal, when done."""
        logger.debug("Download %s", url)
        self.worker = Worker(url=url, timeout=timeout)
        self.worker.com.on_download_finished.connect(self.com.on_download_finished)
        self.worker.com.on_download_failed.connect(self.com.on_download_failed)
        self.threadpool.start(self.worker)
