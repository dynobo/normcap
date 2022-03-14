"""Find new version on github or pypi."""
# TODO: Can be removed?

import logging

import requests
from PySide6 import QtCore

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

    def get(self, url: str):
        """Start downloading url. Emits signal, when done."""
        logger.debug("Download %s", url)
        try:
            response = requests.get(url, timeout=3)
            response.raise_for_status()
            self.com.on_download_finished.emit(response.text)
        except requests.exceptions.RequestException as e:
            logger.error("Download failed due to %s", e)
            self.com.on_download_failed.emit()
