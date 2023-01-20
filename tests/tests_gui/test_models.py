from PySide6 import QtGui

from normcap.gui.models import Capture, Rect, Screen


def test_rect_properties():
    rect = Rect(left=10, top=20, right=110, bottom=220)
    assert rect.width == 100
    assert rect.height == 200
    assert rect.points == (10, 20, 110, 220)
    assert rect.geometry == (10, 20, 100, 200)
    assert rect.size == (100, 200)
    assert "=10" in str(rect)
    assert "=20" in str(rect)
    assert "=110" in str(rect)
    assert "=220" in str(rect)


def test_rect_scaled():
    rect = Rect(left=0, top=0, right=100, bottom=60)
    rect_scaled = rect.scaled(1.5)
    assert rect_scaled.points == (0, 0, 150, 90)

    rect = Rect(left=1, top=1, right=2, bottom=2)
    rect_scaled = rect.scaled(1.5)
    assert rect_scaled.points == (1, 1, 3, 3)


def test_capture_image_area(capture: Capture):
    capture.image = QtGui.QImage(200, 300, QtGui.QImage.Format.Format_RGB32)
    assert capture.image_area == 60_000

    capture.image = QtGui.QImage()
    assert capture.image_area == 0


def test_screen_properties():
    screen = Screen(
        is_primary=True, device_pixel_ratio=2, rect=Rect(0, 0, 1920, 1080), index=1
    )

    assert screen.width == 1920
    assert screen.height == 1080
