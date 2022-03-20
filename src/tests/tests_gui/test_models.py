from PySide6 import QtGui

from normcap.gui.models import Capture, Rect, Screen, Selection


def test_rect_properties():
    rect = Rect(left=10, top=20, right=110, bottom=220)
    assert rect.width == 100
    assert rect.height == 200
    assert rect.points == (10, 20, 110, 220)
    assert rect.geometry == (10, 20, 100, 200)
    assert "=10" in str(rect)
    assert "=20" in str(rect)
    assert "=110" in str(rect)
    assert "=220" in str(rect)


def test_selection_init():
    selection = Selection()
    assert selection.start_x == selection.end_x == 0
    assert selection.start_y == selection.end_y == 0
    assert selection.rect.geometry == (0, 0, 0, 0)
    assert selection.scaled_rect.geometry == (0, 0, 0, 0)


def test_selection_normalize():
    selection = Selection(start_x=100, end_x=0, start_y=50, end_y=0)
    assert selection.rect.points == (0, 0, 100, 50)


def test_selection_scale():
    selection = Selection(start_x=100, end_x=0, start_y=60, end_y=0)
    selection.scale_factor = 1.5
    assert selection.rect.points == (0, 0, 100, 60)
    assert selection.scaled_rect.points == (0, 0, 150, 90)


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
