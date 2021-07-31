"""Find new version on github or pypi."""
import json
import re

from PySide2 import QtCore, QtNetwork

from normcap import __version__
from normcap.logger import logger
from normcap.models import URLS


class Downloader(QtCore.QObject):
    """Downloader using QNetworkAccessManager.

    It is async (provides signal) and avoids an issue on MacOS, where the import
    of urllib.request fails with "no module named _scproxy" in the packaged version.
    """

    onDownloadFinished = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        self.manager = QtNetwork.QNetworkAccessManager()
        self.manager.finished.connect(self._on_get_done)  # pylint: disable=no-member

    def get(self, url: str):
        """Start downloading url. Emits signal, when done."""
        logger.debug(f"Download {url}")
        request = QtNetwork.QNetworkRequest(QtCore.QUrl(url))
        self.manager.get(request)

    def _on_get_done(self, reply):
        """Decode response and emit download finished signal."""
        er = reply.error()
        if er != QtNetwork.QNetworkReply.NoError:
            logger.error(f"Error occurred during download {er}: {reply.errorString()}")
            return

        bytes_string = reply.readAll()
        source = str(bytes_string, "utf-8")

        self.onDownloadFinished.emit(source)


class UpdateChecker(QtCore.QObject):
    """Helper to check for a new version."""

    onVersionRetrieved = QtCore.Signal(str)

    def __init__(self, packaged: bool = False):
        super().__init__()
        self.downloader = Downloader()
        self.packaged = packaged

    def _check_if_new(self, text: str):
        """Check if retrieved version is new."""
        newest_version = self._parse_response(text)
        logger.debug(f"Version found: {newest_version} (installed={__version__}).")
        if newest_version not in ["", __version__]:
            self.onVersionRetrieved.emit(newest_version)  # type: ignore

    def _parse_response(self, text: str):
        """Parse the tag version from the response and emit version retrieved signal."""
        newest_version = ""

        try:
            if self.packaged:
                match = re.search(r'title="v(\d+\.\d+\.\d+.*)"|$', text)
                if match and match.group(1):
                    newest_version = match.group(1)
            else:
                data = json.loads(text)
                newest_version = data["info"]["version"].strip()
        except Exception:  # pylint: disable=broad-except
            logger.exception("Couldn't parse update check response.")

        if newest_version == "":
            logger.error("Couldn't parse newest version.")

        return newest_version

    def check(self):
        """Start the update check."""
        url = URLS.releases if self.packaged else f"{URLS.pypi}/json"

        logger.debug(f"Search for new version on {url}")
        self.downloader.onDownloadFinished.connect(self._check_if_new)
        self.downloader.get(url)
