import sys

import pytest
from PySide6 import QtGui

from normcap.screenshot.handlers.qt import capture
from normcap.system import info


@pytest.mark.gui
@pytest.mark.skipif(
    info.has_wayland_display_manager(), reason="Non-Wayland specific test"
)
@pytest.mark.skipif(
    sys.platform == "darwin",
    reason="Requires granting macOS 'Screen Recording' permission.",
)  # ONHOLD: Check if still necessary with PySide > 6.12
def test_capture_on_non_wayland(qapp):
    # GIVEN any operating system
    # WHEN screenshot is taking using QT
    images = capture()
    # THEN there should be at least one image
    assert images
    assert all(isinstance(i, QtGui.QImage) for i in images)
    # AND the size should not be (0, 0). Qt >= 6.12 captures via ScreenCaptureKit on
    # macOS, which returns empty images without the screen recording permission.
    assert all(i.size().toTuple() != (0, 0) for i in images)


@pytest.mark.gui
@pytest.mark.skipif(
    not info.has_wayland_display_manager(), reason="Wayland specific test"
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
