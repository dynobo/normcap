from PySide2 import QtGui

from normcap.models import Capture, Rect

# pylint: disable=unused-import
from .fixtures import capture

# Allow pytest fixtures:
# pylint: disable=redefined-outer-name
# Allow usint privates:
# pylint: disable=protected-access


def test_rect():
    """Check if calulated properties are working correctely."""
    rect = Rect(left=10, top=20, right=110, bottom=220)
    assert rect.width == 100
    assert rect.height == 200
    assert rect.points == (10, 20, 110, 220)
    assert rect.geometry == (10, 20, 100, 200)


def test_capture(capture: Capture):
    """Check if calulated properties are working correctely."""
    capture.image = QtGui.QImage(200, 300, QtGui.QImage.Format.Format_RGB32)
    capture.image.fill(QtGui.QColor("#ff0000"))

    string = str(capture)
    for field in capture.__dict__:
        assert field in string

    assert capture.image_area == 60_000
    capture.image = QtGui.QImage()
    assert capture.image_area == 0

    assert isinstance(capture.text, str)
    assert capture.text.count("\n") == 0
    assert capture.text.count(" ") >= 2
    assert capture.text.startswith("one")

    assert isinstance(capture.lines, str)
    lines = capture.lines.splitlines()
    assert len(lines) == 2
    assert lines[0] == "one two"

    assert capture.num_blocks == 2
    assert capture.num_pars == 3
    assert capture.num_lines == 2

    assert capture.mean_conf == 30
    capture.words = []
    assert capture.mean_conf == 0

    capture.image = None  # type: ignore
    assert capture.image_area == 0
