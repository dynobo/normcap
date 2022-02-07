import logging
import os
import sys
import textwrap

from PySide6 import QtCore

from normcap.gui.models import Capture, CaptureMode
from normcap.gui.utils import get_icon

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    """Notifier's communication bus."""

    on_notification_sent = QtCore.Signal()


class Notifier(QtCore.QObject):
    """Sends notifications."""

    def __init__(self, parent):
        super().__init__(parent)
        self.com = Communicate()

    def send_notification(self, capture: Capture):
        """Show tray icon then send notification."""
        logger.debug("Send notification")
        on_windows = sys.platform == "win32"
        icon_file = "normcap.png" if on_windows else "tray.png"
        notification_icon = get_icon(icon_file, "tool-magic-symbolic")

        title, message = self.compose_notification(capture)
        self.parent().tray.show()
        self.parent().tray.showMessage(title, message, notification_icon)

        # Delay quit or hide to get notification enough time to show up.
        delay = 5000 if sys.platform == "win32" else 500
        QtCore.QTimer.singleShot(delay, self.com.on_notification_sent.emit)

    @staticmethod
    def compose_notification(capture) -> tuple[str, str]:
        """Extract message text out of captures object and include icon."""
        # Message text
        text = capture.ocr_text.replace(os.linesep, " ")
        text = textwrap.shorten(text, width=45)
        if len(text) < 1:
            text = "Please try again."

        # Message title
        title = ""
        count = 0
        if len(capture.ocr_text) < 1:
            title += "Nothing!"
        elif capture.ocr_applied_magic == "ParagraphMagic":
            count = capture.ocr_text.count(os.linesep * 2) + 1
            title += f"{count} paragraph"
        elif capture.ocr_applied_magic == "EmailMagic":
            count = capture.ocr_text.count("@")
            title += f"{count} email"
        elif capture.ocr_applied_magic == "SingleLineMagic":
            count = capture.ocr_text.count(" ") + 1
            title += f"{count} word"
        elif capture.ocr_applied_magic == "MultiLineMagic":
            count = capture.ocr_text.count("\n") + 1
            title += f"{count} line"
        elif capture.ocr_applied_magic == "UrlMagic":
            count = capture.ocr_text.count("\n") + 1
            title += f"{count} URL"
        elif capture.mode == CaptureMode.RAW:
            count = len(capture.ocr_text)
            title += f"{count} char"
        title += f"{'s' if count > 1 else ''} captured"

        return title, text
