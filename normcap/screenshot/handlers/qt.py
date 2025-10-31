import logging

from PySide6 import QtGui, QtWidgets

from normcap.system import info

logger = logging.getLogger(__name__)

install_instructions = ""


def is_compatible() -> bool:
    return not info.has_wayland_display_manager()


def is_installed() -> bool:
    return True


def capture() -> list[QtGui.QImage]:
    """Capture screenshot with QT method and Screen object.

    Works well on X11, fails on multi monitor macOS.
    """
    images = []
    for screen in QtWidgets.QApplication.screens():
        screenshot = QtGui.QScreen.grabWindow(screen, 0)
        image = screenshot.toImage()
        images.append(image)
    return images
