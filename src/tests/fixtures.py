import pytest  # type: ignore
from PySide6 import QtGui

from normcap.gui.models import Capture, CaptureMode, Rect


@pytest.fixture(scope="session")
def capture() -> Capture:
    """Create argparser and provide its default values."""
    image = QtGui.QImage(200, 300, QtGui.QImage.Format.Format_RGB32)
    image.fill(QtGui.QColor("#ff0000"))
    # draw.rectangle((0, 0, 200, 160), fill=(0, 254, 0))

    return Capture(
        mode=CaptureMode.PARSE,
        rect=Rect(20, 30, 220, 330),
        ocr_text="one two three",
        ocr_applied_magic="",
        image=image,
    )
