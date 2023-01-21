"""Find new version on github or pypi."""
import logging
import re

from PySide6 import QtCore, QtGui, QtWidgets

from normcap import __version__
from normcap.gui.constants import INFO_UPDATE_GITHUB, INFO_UPDATE_PIP, URLS
from normcap.gui.downloader import Downloader

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    """TrayMenus' communication bus."""

    on_version_checked = QtCore.Signal(str)  # newest available version
    on_click_get_new_version = QtCore.Signal(str)  # url to new version


class UpdateChecker(QtCore.QObject):
    """Check for a new normcap version."""

    def __init__(self, parent: QtCore.QObject, packaged: bool = False) -> None:
        super().__init__(parent)
        self.packaged = packaged
        self.com = Communicate()
        self.downloader = Downloader()
        self.downloader.com.on_download_finished.connect(self._on_download_finished)
        self.message_box = self._create_message_box()

    @QtCore.Slot(bytes, str)
    def _on_download_finished(self, data: bytes, url: str) -> None:
        """Parse the tag version from the response and emit version retrieved signal."""
        newest_version = None
        try:
            text = data.decode("utf-8", "ignore")
            if self.packaged:
                regex = r"/releases/tag/v(\d+\.\d+\.\d+)\""  # atom
            else:
                regex = r"\"version\":\s*\"(\d+\.\d+\.\d+)\""  # json

            match = re.search(regex, text)
            if match and match[1]:
                newest_version = match[1]
        except Exception as e:
            logger.exception("Parsing response of update check failed: %s", e)

        if newest_version:
            logger.debug(
                "Newest version: %s (installed: %s)", newest_version, __version__
            )
            self.com.on_version_checked.emit(newest_version)
            if self._is_new_version(current=__version__, other=newest_version):
                self._show_update_message(new_version=newest_version)
        else:
            logger.error("Couldn't detect remote version. Update check won't work!")

    @staticmethod
    def _create_message_box() -> QtWidgets.QMessageBox:
        message_box = QtWidgets.QMessageBox()

        # Necessary on wayland for main window to regain focus:
        message_box.setWindowFlags(QtCore.Qt.WindowType.Popup)

        message_box.setIconPixmap(QtGui.QIcon(":normcap").pixmap(48, 48))
        message_box.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Ok
            | QtWidgets.QMessageBox.StandardButton.Cancel
        )
        message_box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Ok)
        return message_box

    @staticmethod
    def _is_new_version(current: str, other: str) -> bool:
        """Compare version strings.

        As the versions compare are within the scope of this project, a simple parsing
        logic will do. It is based on the assumption that semver and only the suffixes
        "alpha" and "beta" are used.

        NOTE: This is not very robust, so do not use elsewhere! But the standard
        solution packaging.version is not used here on purpose to avoid that dependency.
        That reduces importtime and package size.
        """
        current_tuple = tuple([c.zfill(8) for c in re.split(r"\.|\-", current)])
        other_tuple = tuple([c.zfill(8) for c in re.split(r"\.|\-", other)])

        # Compare just the major.minor.patch for the clear cases
        if other_tuple[:3] > current_tuple[:3]:
            return True

        if other_tuple[:3] < current_tuple[:3]:
            return False

        if len(other_tuple) == 3 and len(current_tuple) == 3:
            return False

        # We have one or more pre-release suffixes to handle.

        # Check if only one version has suffix, which also is a clear case:
        if len(other_tuple) != len(current_tuple):
            return len(other_tuple) < len(current_tuple)

        # Check if the suffix (alpha, beta) are different by comparing first letters
        if current_tuple[3][0] != other_tuple[3][0]:
            return other_tuple[3][0] > current_tuple[3][0]

        # Suffixes are the same, compare numbers
        current_suffix_digits = re.sub(r"[^0-9]", "", current_tuple[3])
        other_suffix_digits = re.sub(r"[^0-9]", "", other_tuple[3])
        return int(other_suffix_digits) > int(current_suffix_digits)

    def _show_update_message(self, new_version: str) -> None:
        """Show dialog informing about available update."""
        text = f"<b>NormCap v{new_version} is available.</b> (You have v{__version__})"
        self.message_box.setText(text)

        info_text = INFO_UPDATE_GITHUB if self.packaged else INFO_UPDATE_PIP
        self.message_box.setInformativeText(info_text)
        self.message_box.setCursor(QtCore.Qt.CursorShape.ArrowCursor)

        choice = self.message_box.exec_()

        if choice == 1024:
            update_url = URLS.releases if self.packaged else URLS.changelog
            self.com.on_click_get_new_version.emit(update_url)

    def check(self) -> None:
        """Start the update check."""
        url = URLS.releases_atom if self.packaged else f"{URLS.pypi_json}"
        logger.debug("Search for new version on %s", url)
        self.downloader.get(url)
