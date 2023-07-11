import sys

import pytest
from PySide6 import QtCore, QtGui

from normcap.gui import models, window


@pytest.mark.skipif(sys.platform == "linux", reason="non-Linux specific test")
def test_move_active_window_to_position_raises_on_non_linux():
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
def test_window_get_scale_factor(qtbot, temp_settings, img_size, screen_size, factor):
    image = QtGui.QImage(*img_size, QtGui.QImage.Format.Format_RGB32)
    screen = models.Screen(
        is_primary=True,
        device_pixel_ratio=1.0,
        rect=models.Rect(0, 0, *screen_size),
        index=0,
        screenshot=image,
    )
    win = window.Window(screen=screen, settings=temp_settings, parent=None)
    qtbot.addWidget(win)

    assert win._get_scale_factor() == factor


def test_window_get_scale_factor_raises_if_missing(qtbot, temp_settings):
    image = QtGui.QImage(600, 400, QtGui.QImage.Format.Format_RGB32)
    screen = models.Screen(
        is_primary=True,
        device_pixel_ratio=1.0,
        rect=models.Rect(0, 0, 600, 400),
        index=0,
        screenshot=image,
    )
    win = window.Window(screen=screen, settings=temp_settings, parent=None)
    qtbot.addWidget(win)

    win.screen_.screenshot = None
    with pytest.raises(ValueError, match="image is missing"):
        _ = win._get_scale_factor()


def test_window_esc_key_pressed(qtbot, temp_settings):
    image = QtGui.QImage(600, 400, QtGui.QImage.Format.Format_RGB32)
    screen = models.Screen(
        is_primary=True,
        device_pixel_ratio=1.0,
        rect=models.Rect(0, 0, 600, 400),
        index=0,
        screenshot=image,
    )
    win = window.Window(screen=screen, settings=temp_settings, parent=None)
    qtbot.add_widget(win)

    # Test propagated, if not selecting
    with qtbot.waitSignal(win.com.on_esc_key_pressed, timeout=2000):
        qtbot.keyPress(win, QtCore.Qt.Key.Key_Escape)

    # Test resets selecting
    win.is_selecting = True
    qtbot.keyPress(win, QtCore.Qt.Key.Key_Escape)
    assert not win.is_selecting
