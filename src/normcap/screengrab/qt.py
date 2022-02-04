"""Some utility functions."""

import logging

from PySide6 import QtGui, QtWidgets

logger = logging.getLogger(__name__)


def grab_screens() -> list[QtGui.QImage]:
    """Capture screenshot with QT method and Screen object.

    Works well on X11, fails on multi monitor MacOS.
    """
    logger.debug("Use capture method: QT")
    images = []
    for screen in QtWidgets.QApplication.screens():
        screenshot = QtGui.QScreen.grabWindow(screen, 0)
        image = screenshot.toImage()
        images.append(image)

    return images
