"""Handler responsible for copying the result to clipboard."""

# Extra
import pyperclip

# Own
from handlers.abstract_handler import AbstractHandler
from data_model import NormcapData


class ClipboardHandler(AbstractHandler):
    def handle(self, request: NormcapData) -> NormcapData:
        """Copy parsed text to clipboard.

        Arguments:
            AbstractHandler {class} -- self
            request {NormcapData} -- NormCap's session data

        Returns:
            NormcapData -- Enriched NormCap's session data
        """
        self._logger.info("Copying to clipboard...")
        pyperclip.copy(request.transformed)

        if self._next_handler:
            return super().handle(request)
        else:
            return request
