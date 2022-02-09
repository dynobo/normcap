import pytest  # type: ignore
from PySide2 import QtGui

from normcap.models import Capture, CaptureMode, Rect

# Allow pytest fixtures:
# pylint: disable=redefined-outer-name
# Allow usint privates:
# pylint: disable=protected-access


@pytest.fixture(scope="session")
def capture() -> Capture:
    """Create argparser and provide its default values."""
    image = QtGui.QImage(200, 300, QtGui.QImage.Format.Format_RGB32)
    image.fill(QtGui.QColor("#ff0000"))
    # draw.rectangle((0, 0, 200, 160), fill=(0, 254, 0))

    return Capture(
        mode=CaptureMode.PARSE,
        rect=Rect(20, 30, 220, 330),
        transformed="",
        best_magic="",
        tess_args=dict(psm=2, lang="eng"),
        image=image,
        words=[
            {
                "level": 1,
                "page_num": 1,
                "block_num": 1,
                "par_num": 1,
                "line_num": 1,
                "word_num": 1,
                "left": 5,
                "top": 0,
                "width": 55,
                "height": 36,
                "conf": 20,
                "text": "one",
            },
            {
                "level": 1,
                "page_num": 1,
                "block_num": 1,
                "par_num": 2,
                "line_num": 1,
                "word_num": 2,
                "left": 5,
                "top": 0,
                "width": 55,
                "height": 36,
                "conf": 40,
                "text": "two",
            },
            {
                "level": 1,
                "page_num": 1,
                "block_num": 2,
                "par_num": 3,
                "line_num": 3,
                "word_num": 3,
                "left": 5,
                "top": 0,
                "width": 55,
                "height": 36,
                "conf": 30,
                "text": "three",
            },
        ],
    )
