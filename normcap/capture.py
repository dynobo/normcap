"""
"""
# Default
import logging

# Extra
import mss
from PIL import Image


class Capture:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def capture_screen(self, selection):
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
                selection.shots.append(shot)

        return selection
