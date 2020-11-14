"""Handler responsible for copying the result to clipboard."""
# Default
import os
import textwrap

# Extra
from notifypy import Notify  # type: ignore
from importlib_resources import files  # type: ignore

# Own
from normcap import __version__
from normcap.common.data_model import NormcapData
from normcap.handlers.abstract_handler import AbstractHandler


class NotificationHandler(AbstractHandler):
    def handle(self, request: NormcapData) -> NormcapData:
        """Trigger system notification when ocr is done.

        Arguments:
            AbstractHandler {class} -- self
            request {NormcapData} -- NormCap's session data

        Returns:
            NormcapData -- Enriched NormCap's session data
        """
        self._logger.info("Sending notification...")
        title, text, icon_path = self.compose_notification(request)
        self._logger.info("Icon path: %s", icon_path)
        if not request.test_mode:
            self.send_notification(title, text, icon_path)

        if self._next_handler:
            return super().handle(request)

        return request

    @staticmethod
    def compose_notification(request):
        """Extract message text out of requests object and include icon."""
        # Message icon, not available for MacOS
        icon_path = None
        if not request.platform.startswith("darwin"):
            icon_path = files("normcap.ressources").joinpath("normcap.png")

        # Message text
        text = request.transformed.replace(os.linesep, " ")
        text = textwrap.shorten(text, width=35)
        if len(text) < 1:
            text = "Please try again."

        # Message title
        title = "Normcap captured "
        count = 0
        if len(request.transformed) < 1:
            title += "nothing!"
        elif request.best_magic == "paragraph":
            count = request.transformed.count(os.linesep * 2) + 1
            title += f"{count} paragraph"
        elif request.best_magic == "email":
            count = request.transformed.count("@")
            title += f"{count} email"
        elif request.best_magic == "single_line":
            count = request.transformed.count(" ") + 1
            title += f"{count} word"
        elif request.best_magic == "multi_line":
            count = request.transformed.count("\n") + 1
            title += f"{count} line"
        title += f"{'s' if count > 1 else ''}"

        return title, text, icon_path

    @staticmethod
    def send_notification(title, text, icon_path):
        """Send notification out

        Args:
            title (str): Notification title
            text (str): Notification text
            icon_path (str): Path to icon shown in the notification
        """
        notification = Notify()
        notification.title = title
        notification.message = text
        notification.application_name = "NormCap v" + __version__
        if icon_path:
            notification.icon = icon_path
        notification.send(block=False)
