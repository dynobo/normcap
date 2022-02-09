import pytest
from PySide6 import QtCore, QtGui

from normcap.gui.models import Capture, Rect, Screen

from ..fixtures import capture  # pylint: disable=unused-import

# Specific settings for pytest
# pylint: disable=redefined-outer-name,protected-access,unused-argument


def test_rect_properties():
    rect = Rect(left=10, top=20, right=110, bottom=220)
    assert rect.width == 100
    assert rect.height == 200
    assert rect.points == (10, 20, 110, 220)
    assert rect.geometry == (10, 20, 100, 200)
    rect.scale(0.5)
    assert rect.geometry == (5, 10, 50, 100)

    rect = Rect(left=20, top=20, right=10, bottom=0)
    assert rect.geometry == (20, 20, -10, -20)
    rect.normalize()
    assert rect.geometry == (10, 0, 10, 20)


def test_capture_image_area(capture: Capture):
    capture.image = QtGui.QImage(200, 300, QtGui.QImage.Format.Format_RGB32)
    assert capture.image_area == 60_000

    capture.image = QtGui.QImage()
    assert capture.image_area == 0


def test_screen_properties():
    screen = Screen(
        is_primary=True, device_pixel_ratio=2, geometry=Rect(0, 0, 1920, 1080), index=1
    )

    assert screen.width == 1920
    assert screen.height == 1080


def test_screen_get_scaled_screenshot():
    screen = Screen(
        is_primary=True, device_pixel_ratio=2, geometry=Rect(0, 0, 1920, 1080), index=1
    )

    # Raise exception if no screenshot in Screen object
    with pytest.raises(TypeError):
        _ = screen.get_scaled_screenshot(QtCore.QSize(160, 90))

    screen.raw_screenshot = QtGui.QImage(1920, 1080, QtGui.QImage.Format.Format_RGB32)

    # Scale to raw image size
    scaled = screen.get_scaled_screenshot(QtCore.QSize(1920, 1080))
    assert scaled == screen.raw_screenshot

    # Scale to smaller size
    scaled = screen.get_scaled_screenshot(QtCore.QSize(192, 108))
    assert scaled == screen.scaled_screenshot
    assert scaled.width() == 192
    assert scaled.height() == 108
    assert screen.screen_window_ratio == 10

    # Scale to same smaller size
    scaled_again = screen.get_scaled_screenshot(QtCore.QSize(192, 108))
    assert scaled == scaled_again
