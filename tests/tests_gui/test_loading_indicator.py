import math

import pytest
from PySide6 import QtGui, QtWidgets

from normcap.gui.loading_indicator import LoadingIndicator


def _convert_to_pixels(image):
    image = image.convertToFormat(QtGui.QImage.Format.Format_RGB32)
    ptr = image.constBits()
    values = list(ptr)
    color_values = [tuple(values[i : i + 4]) for i in range(0, len(values), 4)]
    # Drop alpha value and return RGB
    return [c[2::-1] for c in color_values]


@pytest.mark.gui()
def test_radius(qtbot):
    # GIVEN an indicator instance with a certain size
    window = QtWidgets.QMainWindow()
    widget_size = 64
    indicator = LoadingIndicator(parent=window, size=widget_size)

    # WHEN the indicator  is created
    qtbot.addWidget(window)

    # THEN the dot radius should be way smaller than half of the widget size
    #    and larger or equal to 1
    assert 1 <= indicator.radius < widget_size / 2


@pytest.mark.gui()
def test_opacities(qtbot):
    # GIVEN an indicator instance
    window = QtWidgets.QMainWindow()
    indicator = LoadingIndicator(parent=window)

    # WHEN creating the indicator
    qtbot.addWidget(window)

    # THEN the number of opacities should be equal to the number of dots
    #    and each opacity should be below the preceding opacity
    opacities = indicator.opacities
    assert len(opacities) == indicator.dot_count
    assert all(opacities[i] < opacities[i - 1] for i in range(1, len(opacities)))


@pytest.mark.gui()
def test_show_starts_timer(qtbot):
    # GIVEN an indicator instance
    window = QtWidgets.QMainWindow()
    indicator = LoadingIndicator(parent=window)
    qtbot.addWidget(window)

    # WHEN showing the indicator including its parent
    window.show()
    indicator.show()

    # THEN the animation timer should start
    assert indicator.timer


@pytest.mark.gui()
def test_hide_stops_timer(qtbot):
    # GIVEN a visible indicator
    window = QtWidgets.QMainWindow()
    indicator = LoadingIndicator(parent=window)
    qtbot.addWidget(window)
    window.show()
    indicator.show()

    # WHEN hiding the indicator with a running time
    assert indicator.timer
    indicator.hide()

    # THEN the animation timer should be reset
    assert indicator.timer is None


@pytest.mark.gui()
def test_frame_count_progresses(monkeypatch, qtbot):
    # GIVEN a indicator with a mocked paintEvent method for to capture counter values
    counter_values = []

    def mocked_paint_event(cls, event):
        counter_values.append(cls.counter)

    monkeypatch.setattr(LoadingIndicator, "paintEvent", mocked_paint_event)
    window = QtWidgets.QMainWindow()
    indicator = LoadingIndicator(parent=window)
    qtbot.addWidget(window)

    # WHEN showing the indicator with a certain framerate and waiting x seconds
    assert indicator.counter == 0
    indicator.framerate = 120
    window.show()
    indicator.show()
    qtbot.wait(800)

    # THEN the counter should have reached the last frame at least once
    assert counter_values
    assert max(counter_values) == indicator.dot_count - 1


@pytest.mark.gui()
def test_circles_are_rendered(qtbot):
    # GIVEN a indicator instance with a red dots are rendered on a black window
    window = QtWidgets.QMainWindow()
    window.setStyleSheet("background-color: black;")
    indicator = LoadingIndicator(parent=window)
    indicator.max_opacity = 255
    indicator.dot_color = (255, 0, 0)
    qtbot.addWidget(window)

    # WHEN showing the indicator, waiting a bit before taking a screenshot
    window.show()
    indicator.show()
    qtbot.wait(100)
    pixmap = QtGui.QPixmap(window.size())
    window.render(pixmap)

    # THEN the the canvas should contain enough pixel close the dot color
    #    (due to the rendering, the pixels don't exactly have the dot color)
    pixels = _convert_to_pixels(pixmap.toImage())
    accepted_threshold = 30
    reddish_pixels = [
        p
        for p in pixels
        if (
            (p[0] > 255 - accepted_threshold)
            and (p[1] < 0 + accepted_threshold)
            and (p[2] < 0 + accepted_threshold)
        )
    ]

    dot_area = math.pi * indicator.radius**2
    accepted_deviation = 0.2
    assert dot_area * (1 + accepted_deviation) > len(reddish_pixels)
    assert dot_area * (1 - accepted_deviation) < len(reddish_pixels)
