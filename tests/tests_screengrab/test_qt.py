import pytest
from PySide6 import QtGui

from normcap.screengrab import utils
from normcap.screengrab.qt import capture


@pytest.mark.gui()
@pytest.mark.skipif(
    utils.is_wayland_display_manager(), reason="Non-Wayland specific test"
)
def test_capture_on_non_wayland(qapp):
    # GIVEN any operating system
    # WHEN screenshot is taking using QT
    images = capture()
    # THEN there should be at least one image
    #   and the size should not be (0, 0)
    assert images
    assert all(isinstance(i, QtGui.QImage) for i in images)
    assert all(i.size().toTuple() != (0, 0) for i in images)


@pytest.mark.gui()
@pytest.mark.skipif(
    not utils.is_wayland_display_manager(), reason="Wayland specific test"
)
def test_capture_on_wayland(qapp):
    # GIVEN any operating system
    # WHEN screenshot is taking using QT
    images = capture()
    # THEN there should be at least one image
    #   and the size should be (0, 0) because qt method return empty image on Wayland
    assert images
    assert all(isinstance(i, QtGui.QImage) for i in images)
    all(i.size().toTuple() == (0, 0) for i in images)
