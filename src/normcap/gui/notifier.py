import os
import textwrap
from typing import Tuple

from PySide2 import QtCore

from normcap.logger import logger
from normcap.models import Capture, CaptureMode, Platform
from normcap.utils import get_icon


class Communicate(QtCore.QObject):
    """Notifier's communication bus."""

    on_notification_sent = QtCore.Signal()


class Notifier(QtCore.QObject):
    """Sends notifications"""

    def __init__(self, parent, platform: Platform):
        super().__init__(parent)
        self.com = Communicate()
        self.platform = platform

    def send_notification(self, capture: Capture):
        """Show tray icon then send notification."""

        on_windows = self.platform == Platform.WINDOWS
        icon_file = "normcap.png" if on_windows else "tray.png"
        notification_icon = get_icon(icon_file, "tool-magic-symbolic")

        title, message = self.compose_notification(capture)
        self.parent().tray.show()
        self.parent().tray.showMessage(title, message, notification_icon)
        logger.debug("Notification sent")

        # Delay quit or hide to get notification enough time to show up.
        delay = 5000 if self.platform == Platform.WINDOWS else 500
        QtCore.QTimer.singleShot(delay, self.com.on_notification_sent.emit)

    @staticmethod
    def compose_notification(capture) -> Tuple[str, str]:
        """Extract message text out of captures object and include icon."""

        # Message text
        text = capture.transformed.replace(os.linesep, " ")
        text = textwrap.shorten(text, width=45)
        if len(text) < 1:
            text = "Please try again."

        # Message title
        title = ""
        count = 0
        if len(capture.transformed) < 1:
            title += "Nothing!"
        elif capture.best_magic == "ParagraphMagic":
            count = capture.transformed.count(os.linesep * 2) + 1
            title += f"{count} paragraph"
        elif capture.best_magic == "EmailMagic":
            count = capture.transformed.count("@")
            title += f"{count} email"
        elif capture.best_magic == "SingleLineMagic":
            count = capture.transformed.count(" ") + 1
            title += f"{count} word"
        elif capture.best_magic == "MultiLineMagic":
            count = capture.transformed.count("\n") + 1
            title += f"{count} line"
        elif capture.best_magic == "UrlMagic":
            count = capture.transformed.count("http")
            title += f"{count} URL"
        elif capture.mode == CaptureMode.RAW:
            count = len(capture.transformed)
            title += f"{count} char"
        title += f"{'s' if count > 1 else ''} captured"

        return title, text
