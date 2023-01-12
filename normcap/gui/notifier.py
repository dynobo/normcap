import logging
import os
import shutil
import subprocess
import sys
import textwrap

from PySide6 import QtCore

from normcap.gui import system_info
from normcap.gui.models import Capture, CaptureMode
from normcap.gui.utils import get_icon

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    """Notifier's communication bus."""

    on_notification_sent = QtCore.Signal()


class Notifier(QtCore.QObject):
    """Sends notifications."""

    def __init__(self, parent: QtCore.QObject) -> None:
        super().__init__(parent)
        self.com = Communicate()

    @staticmethod
    def _compose_notification(capture: Capture) -> tuple[str, str]:
        """Extract message text out of captures object and include icon."""
        # Compose message text
        if not capture.ocr_text or len(capture.ocr_text.strip()) < 1:
            title = "Nothing captured!"
            text = "Please try again."
            return title, text

        text = capture.ocr_text.strip().replace(os.linesep, " ")
        text = textwrap.shorten(text, width=45)

        # Compose message title
        if capture.ocr_applied_magic == "ParagraphMagic":
            count = capture.ocr_text.count(os.linesep * 2) + 1
            title = f"{count} paragraph"
        elif capture.ocr_applied_magic == "EmailMagic":
            count = capture.ocr_text.count("@")
            title = f"{count} email"
        elif capture.ocr_applied_magic == "SingleLineMagic":
            count = capture.ocr_text.count(" ") + 1
            title = f"{count} word"
        elif capture.ocr_applied_magic == "MultiLineMagic":
            count = capture.ocr_text.count("\n") + 1
            title = f"{count} line"
        elif capture.ocr_applied_magic == "UrlMagic":
            count = capture.ocr_text.count("\n") + 1
            title = f"{count} URL"
        elif capture.mode == CaptureMode.RAW:
            count = len(capture.ocr_text)
            title = f"{count} char"
        else:
            count = 0
            title = ""

        title += f"{'s' if count > 1 else ''} captured"

        return title, text

    def send_notification(self, capture: Capture) -> None:
        """Show tray icon then send notification."""
        title, message = self._compose_notification(capture)
        if sys.platform == "linux" and shutil.which("notify-send"):
            self.send_via_libnotify(title, message)
        else:
            self.send_via_qt_tray(title, message)
        self.com.on_notification_sent.emit()

    def send_via_libnotify(self, title: str, message: str) -> None:
        """Sending via notify-send.

        Seems to work more reliable on Linux + Gnome, but requires libnotify.
        Running in detached mode to avoid freezing KDE bar in some distributions.
        """
        logger.debug("Send notification using notify-send.")
        icon_path = system_info.get_resources_path() / "normcap.png"

        # Escape chars interpreted by notifiy-send
        message = message.replace("\\", "\\\\")
        message = message.replace("-", "\\-")

        cmds = [
            "notify-send",
            f"--icon={icon_path.resolve()}",
            "--app-name=NormCap",
            f"{title}",
            f"{message}",
        ]

        # Left detached on purpose!
        subprocess.Popen(cmds, start_new_session=True)

    def send_via_qt_tray(self, title: str, message: str) -> None:
        """Sending via QT trayicon.

        Used for:
            - Windows
            - macOS
            - Linux (Fallback in case no notify-send)
        """
        logger.debug("Send notification using QT showMessage.")
        notification_icon = get_icon("normcap")
        self.parent().show()
        self.parent().showMessage(title, message, notification_icon)
