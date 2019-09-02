"""
"""

# Extra
import pyperclip

# Own
from handler import AbstractHandler
from data_model import NormcapData


class ClipboardHandler(AbstractHandler):
    def handle(self, request: NormcapData) -> NormcapData:
        self._logger.info("Copying to clipboard...")

        # Check available OCR
        pyperclip.copy(request.text)

        if self._next_handler:
            return super().handle(request)
        else:
            return request
