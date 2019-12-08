"""Unit tests for screenshot capture handler."""

# Extra
from PIL import Image
from mss.exception import ScreenShotError

# Own
from normcap.common.data_model import NormcapData
from normcap.handlers.capture_handler import CaptureHandler


def test_capture_handler():
    """Test if screenshots are added to data object."""
    data = NormcapData()
    try:
        capture = CaptureHandler()
        result = capture.handle(data)
        assert (len(result.shots) > 0) and (
            isinstance(result.shots[0]["image"], Image.Image)
        )
    except ScreenShotError:
        # We get this error if e.g. no Xserver is available.
        # Fallback to test_mode, as needed by github actions
        capture = CaptureHandler()
        data.test_mode = True
        result = capture.handle(data)
        assert (len(result.shots) > 0) and (
            isinstance(result.shots[0]["image"], Image.Image)
        )
