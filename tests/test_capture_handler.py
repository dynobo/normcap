"""Unit tests for screenshot capture handler."""
# Default
import os

# Extra
from PIL import Image
from mss.exception import ScreenShotError

# Own
from normcap.common.data_model import NormcapData
from normcap.handlers.capture_handler import CaptureHandler


def test_capture_handler():
    """Test if screenshots are added to data object."""
    data = NormcapData()
    capture = CaptureHandler()
    try:
        result = capture.handle(data)
        assert (len(result.shots) > 0) and (
            isinstance(result.shots[0]["image"], Image.Image)
        )
    except ScreenShotError:
        # We expect this error if no Xserver is available:
        x_available = False
        if "DISPLAY" in os.environ:
            print("\nWARNING: Exception, but X seems running!\n")
            x_available = True
        assert x_available is False
