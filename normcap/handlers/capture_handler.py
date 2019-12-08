"""Handler responsible for attaching screenshot(s) to session data."""

# Extra
import mss  # type: ignore
from PIL import Image  # type: ignore

# Own
from normcap.common.data_model import NormcapData
from normcap.common.utils import log_dataclass
from normcap.handlers.abstract_handler import AbstractHandler


class CaptureHandler(AbstractHandler):
    def handle(self, request: NormcapData) -> NormcapData:
        """Take multimon screenshots and add those images to session data.

        Arguments:
            AbstractHandler {class} -- self
            request {NormcapData} -- NormCap's session data

        Returns:
            NormcapData -- Enriched NormCap's session data
        """
        self._logger.info("Taking Screenshot(s)...")

        if not request.test_mode:
            request = self._take_screeshot(request)
        else:
            self._logger.info("Test mode. Using existing screenshot...")

        if self._next_handler:
            return super().handle(request)
        else:
            return request

    def _take_screeshot(self, request):
        with mss.mss() as sct:
            # Grab screens of all monitors
            for idx, position in enumerate(sct.monitors[1:]):

                raw = sct.grab(position)

                # Convert to Pil
                img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

                # Append list with screenshots
                shot = {"monitor": idx, "image": img, "position": position}
                request.shots.append(shot)

        log_dataclass("Dataclass after screenshot added:", request)
        return request
