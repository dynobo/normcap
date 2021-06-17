"""Handler responsible for copying the result to clipboard."""
import contextlib
import io

import pyclip  # type: ignore

from normcap.common.data_model import NormcapData
from normcap.handlers.abstract_handler import AbstractHandler


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

        # supress output triggered somewhere in pypeclip
        with contextlib.redirect_stdout(io.StringIO()):
            pyclip.copy(request.transformed, encoding="utf-8")

        if self._next_handler:
            return super().handle(request)
        else:
            return request
