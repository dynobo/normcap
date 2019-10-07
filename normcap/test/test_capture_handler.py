"""Unit tests for screenshot capture handler."""

# Extra
from PIL import Image

# Own
from normcap.data_model import NormcapData
from normcap.handlers.capture_handler import CaptureHandler


def test_capture_handler():
    """Test if screenshots are added to data object."""
    data = NormcapData()
    capture = CaptureHandler()
    result = capture.handle(data)
    assert (len(result.shots) > 0) and (
        isinstance(result.shots[0]["image"], Image.Image)
    )
