"""
"""
# Extra
import mss
from PIL import Image

# Own
from handlers.abstract_handler import AbstractHandler
from data_model import NormcapData
from utils import log_dataclass


class CaptureHandler(AbstractHandler):
    def handle(self, request: NormcapData) -> NormcapData:
        self._logger.info("Taking Screenshot(s)...")

        with mss.mss() as sct:
            # Grab all screens
            for idx, position in enumerate(sct.monitors[1:]):
                # Capture
                raw_shot = sct.grab(position)

                # Convert to Pil
                img = Image.frombytes(
                    "RGB", raw_shot.size, raw_shot.bgra, "raw", "BGRX"
                )

                # Append list with screenshots
                shot = {"monitor": idx, "image": img, "position": position}
                request.shots.append(shot)

        self._logger.debug("Dataclass after screenshot added:")
        log_dataclass(request)

        if self._next_handler:
            return super().handle(request)
        else:
            return request
