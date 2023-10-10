import pytest
from PySide6 import QtGui

from normcap.gui.models import Capture, Rect, Screen


def test_rect_properties():
    # GIVEN an initialized rect
    rect = Rect(left=10, top=20, right=110, bottom=220)

    # WHEN properties are accessed
    # THEN they should return correct values
    assert rect.width == 101
    assert rect.height == 201
    assert rect.coords == (10, 20, 110, 220)
    assert rect.geometry == (10, 20, 101, 201)
    assert rect.size == (101, 201)
    assert "=10" in str(rect)
    assert "=20" in str(rect)
    assert "=110" in str(rect)
    assert "=220" in str(rect)


@pytest.mark.parametrize(
    ("coords", "factor", "expected_scaled_coords"),
    [
        ((0, 0, 100, 60), 1.5, (0, 0, 150, 90)),
        ((1, 1, 2, 2), 1.5, (1, 1, 3, 3)),
        ((10, 20, 110, 220), 2, (20, 40, 220, 440)),
    ],
)
def test_rect_scaled_coords(coords, factor, expected_scaled_coords):
    # GIVEN a Rect is instantiated with certain coords
    rect = Rect(*coords)

    # WHEN it gets scaled through its method
    rect_scaled = rect.scale(factor)

    # THEN it should result in certain scaled coords
    assert rect_scaled.coords == expected_scaled_coords


@pytest.mark.parametrize(
    ("width", "height", "expected_area"), [(200, 300, (200 + 1) * (300 + 1)), (0, 0, 0)]
)
def test_capture_image_area(capture: Capture, width, height, expected_area):
    # GIVEN a Capture is instantiated with an image of certain dimension
    capture.image = QtGui.QImage(width, height, QtGui.QImage.Format.Format_RGB32)

    # WHEN the image are is accessed
    # THEN it should return the correct value
    assert capture.image_area == expected_area


def test_screen_properties():
    # GIVEN a Screen is instantiated with certain rect information
    screen = Screen(
        device_pixel_ratio=2, left=0, top=0, right=1920, bottom=1080, index=1
    )

    # WHEN properties are accessed
    # THEN they should return correct values
    assert screen.width == 1921
    assert screen.height == 1081
    assert screen.size == (1921, 1081)


@pytest.mark.parametrize(
    ("coords", "device_pixel_ratio", "factor", "expected_scaled_coords"),
    [
        ((0, 0, 1920, 1080), 2, 1.5, (0, 0, 2880, 1620)),
        ((0, 0, 1920, 1080), 2, None, (0, 0, 960, 540)),
        ((10, 20, 110, 220), 1, 2, (20, 40, 220, 440)),
        ((1920, 1080, 2520, 1480), 2, 1, (1920, 1080, 2520, 1480)),
        ((1920, 1080, 2520, 1480), 2, None, (960, 540, 1260, 740)),
    ],
)
def test_screen_scale_coords(
    coords, device_pixel_ratio, factor, expected_scaled_coords
):
    # GIVEN a Screen is instantiated with certain coords and DPR
    screen = Screen(
        device_pixel_ratio=device_pixel_ratio,
        left=coords[0],
        top=coords[1],
        right=coords[2],
        bottom=coords[3],
        index=1,
    )

    # WHEN it gets scaled through its method
    screen_scaled = screen.scale(factor)

    # THEN it should result in certain scaled coords
    assert screen_scaled.coords == expected_scaled_coords
