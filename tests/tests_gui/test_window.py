import sys

import pytest
from PySide6 import QtGui

from normcap.gui import models, window


def test_move_active_window_to_position_raises_on_non_linux():
    if not sys.platform.startswith("win"):
        pytest.xfail("Windows specific test")

    rect = models.Rect()

    with pytest.raises(TypeError, match="should only be called on Linux"):
        window._move_active_window_to_position_on_gnome(rect)

    with pytest.raises(TypeError, match="should only be called on Linux"):
        window._move_active_window_to_position_on_kde(rect)


@pytest.mark.parametrize(
    ("img_size", "screen_size", "factor"),
    [
        ((600, 400), (600, 400), 1.0),
        ((300, 200), (600, 400), 0.5),
        ((1200, 800), (600, 400), 2.0),
    ],
)
def test_window_get_scale_factor(qapp, temp_settings, img_size, screen_size, factor):
    image = QtGui.QImage(*img_size, QtGui.QImage.Format.Format_RGB32)
    screen = models.Screen(
        is_primary=True,
        device_pixel_ratio=1.0,
        rect=models.Rect(0, 0, *screen_size),
        index=0,
        screenshot=image,
    )
    win = window.Window(screen=screen, settings=temp_settings)

    assert win._get_scale_factor() == factor


def test_window_get_scale_factor_raises_if_missing(qapp, temp_settings):
    image = QtGui.QImage(600, 400, QtGui.QImage.Format.Format_RGB32)
    screen = models.Screen(
        is_primary=True,
        device_pixel_ratio=1.0,
        rect=models.Rect(0, 0, 600, 400),
        index=0,
        screenshot=image,
    )
    win = window.Window(screen=screen, settings=temp_settings)
    win.screen_.screenshot = None
    with pytest.raises(ValueError, match="image is missing"):
        _ = win._get_scale_factor()
