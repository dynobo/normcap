"""Find new version on github or pypi."""
import json
import re

from PySide2 import QtCore, QtWidgets

from normcap import __version__
from normcap.gui.downloader import Downloader
from normcap.logger import logger
from normcap.models import URLS
from normcap.utils import get_icon, set_cursor


class Communicate(QtCore.QObject):
    """TrayMenus' communication bus."""

    on_version_retrieved = QtCore.Signal(str)
    on_click_get_new_version = QtCore.Signal(str)


class UpdateChecker(QtCore.QObject):
    """Helper to check for a new version."""

    def __init__(self, parent, packaged: bool = False):
        super().__init__(parent)
        self.packaged = packaged
        self.com = Communicate()
        self.downloader = Downloader()
        self.downloader.com.on_download_finished.connect(self._check_if_new)

    def _check_if_new(self, text: str):
        """Check if retrieved version is new."""
        newest_version = self._parse_response(text)
        logger.debug(f"Version found: {newest_version} (installed={__version__})")
        if newest_version not in ["", __version__]:
            self.com.on_version_retrieved.emit(newest_version)

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
            logger.exception("Couldn't parse update check response")

        if newest_version == "":
            logger.error("Couldn't parse newest version")

        return newest_version

    def check(self):
        """Start the update check."""
        url = URLS.releases if self.packaged else f"{URLS.pypi}/json"
        logger.debug(f"Search for new version on {url}")
        self.downloader.get(url)

    def show_update_message(self, new_version):
        """Show dialog informing about available update."""

        text = f"<b>NormCap v{new_version} is available.</b> (You have v{__version__})"
        if self.packaged:
            info_text = (
                "You can download the new version for your operating system from "
                "GitHub.\n\n"
                "Do you want to visit the release website now?"
            )
        else:
            info_text = (
                "You should be able to upgrade from command line with "
                "'pip install normcap --upgrade'.\n\n"
                "Do you want to visit the release website now?"
            )

        message_box = QtWidgets.QMessageBox()

        # Necessary on wayland for main window to regain focus:
        message_box.setWindowFlags(QtCore.Qt.Popup)

        message_box.setIconPixmap(get_icon("normcap.png").pixmap(48, 48))
        message_box.setText(text)
        message_box.setInformativeText(info_text)
        message_box.setStandardButtons(
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
        )
        message_box.setDefaultButton(QtWidgets.QMessageBox.Ok)

        set_cursor(QtCore.Qt.ArrowCursor)
        choice = message_box.exec_()
        set_cursor(QtCore.Qt.CrossCursor)

        if choice == 1024:
            self.com.on_click_get_new_version.emit(URLS.releases)
