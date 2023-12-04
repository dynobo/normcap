import sys

import pytest
from PySide6 import QtCore, QtGui

from normcap.gui import models, window


@pytest.mark.skipif(sys.platform == "linux", reason="non-Linux specific test")
def test_move_active_window_to_position_raises_on_non_linux():
    # GIVEN a non-Linux system

    # WHEN a function to move the active window is called

    # THEN an exception should be raised, because those functions are not supposed to
    #   work on a non-Linux system
    rect = models.Rect(left=0, top=0, right=0, bottom=0)

    with pytest.raises(TypeError, match="should only be called on Linux"):
        window._move_active_window_to_position_on_gnome(rect)

    with pytest.raises(TypeError, match="should only be called on Linux"):
        window._move_active_window_to_position_on_kde(rect)


@pytest.mark.gui()
@pytest.mark.parametrize(
    ("img_size", "window_size", "expected_factor"),
    [
        ((600, 400), (600, 400), 1.0),
        ((300, 200), (600, 400), 0.5),
        ((1200, 800), (600, 400), 2.0),
    ],
)
def test_window_get_scale_factor(
    qtbot, temp_settings, img_size, window_size, expected_factor
):
    # GIVEN a screenshot of a certain size
    #   and a certain (Qt) screen size
    image = QtGui.QImage(QtCore.QSize(*img_size), QtGui.QImage.Format.Format_RGB32)
    screen = models.Screen(
        device_pixel_ratio=1.0,
        left=0,
        top=0,
        right=window_size[0] - 1,
        bottom=window_size[1] - 1,
        index=0,
        screenshot=image,
    )

    # WHEN the window is created
    win = window.Window(screen=screen, settings=temp_settings, parent=None)
    win.resize(QtCore.QSize(*window_size))

    # THEN the expected scaling factor should be calculated
    assert win._get_scale_factor() == expected_factor


@pytest.mark.gui()
def test_window_get_scale_factor_raises_if_missing(qtbot, temp_settings):
    # GIVEN a certain (Qt) screen size
    image = QtGui.QImage(QtCore.QSize(640, 480), QtGui.QImage.Format.Format_RGB32)
    screen = models.Screen(
        device_pixel_ratio=1.0,
        left=0,
        top=0,
        right=600,
        bottom=400,
        index=0,
        screenshot=image,
    )

    # WHEN the window is created
    #   and the screenshot is not available (anymore)
    win = window.Window(screen=screen, settings=temp_settings, parent=None)
    win.screen_.screenshot = None

    # THEN an exception should be raised when trying to calculate the scale factor
    with pytest.raises(ValueError, match="image is missing"):
        _ = win._get_scale_factor()


@pytest.mark.gui()
def test_window_esc_key_pressed(qtbot, temp_settings):
    # GIVEN a window is shown
    #   with a screenshot of a certain size
    #   on a certain (Qt) screen size
    image = QtGui.QImage(600, 400, QtGui.QImage.Format.Format_RGB32)
    screen = models.Screen(
        device_pixel_ratio=1.0,
        left=0,
        top=0,
        right=600,
        bottom=400,
        index=0,
        screenshot=image,
    )
    win = window.Window(screen=screen, settings=temp_settings, parent=None)
    qtbot.add_widget(win)

    # WHEN nothing is selected and  the ESC key is pressed
    # THEN the appropriate signal should be triggered
    with qtbot.waitSignal(win.com.on_esc_key_pressed, timeout=1000):
        qtbot.keyPress(win, QtCore.Qt.Key.Key_Escape)


@pytest.mark.gui()
def test_window_esc_key_pressed_while_selecting(qtbot, temp_settings):
    # GIVEN a window is shown
    #   with a screenshot of a certain size
    #   on a certain (Qt) screen size
    image = QtGui.QImage(600, 400, QtGui.QImage.Format.Format_RGB32)
    screen = models.Screen(
        device_pixel_ratio=1.0,
        left=0,
        top=0,
        right=600,
        bottom=400,
        index=0,
        screenshot=image,
    )
    win = window.Window(screen=screen, settings=temp_settings, parent=None)
    qtbot.add_widget(win)

    # WHEN a region is currently selected
    #   and the ESC key is pressed
    qtbot.mousePress(win, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(10, 10))
    qtbot.mouseMove(win, pos=QtCore.QPoint(30, 30))
    assert win.selection_rect
    qtbot.keyPress(win, QtCore.Qt.Key.Key_Escape)

    # THEN the selection should be cleared
    assert not win.selection_rect


def test_window_get_capture_mode_fallback_to_parse(temp_settings, caplog):
    # GIVEN a window with an invalid mode setting
    image = QtGui.QImage(600, 400, QtGui.QImage.Format.Format_RGB32)
    screen = models.Screen(
        device_pixel_ratio=1.0,
        left=0,
        top=0,
        right=600,
        bottom=400,
        index=0,
        screenshot=image,
    )
    invalid_mode = "some_deprecated_mode"
    temp_settings.setValue("mode", invalid_mode)
    win = window.Window(screen=screen, settings=temp_settings, parent=None)

    # WHEN the capture mode is read
    mode = win.get_capture_mode()

    # THEN a warning should be logged
    #    and "parse" mode should be returned as fallback
    assert "warning" in caplog.text.lower()
    assert "unknown capture mode" in caplog.text.lower()
    assert invalid_mode in caplog.text.lower()
    assert mode == models.CaptureMode.PARSE
