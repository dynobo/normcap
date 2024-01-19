import logging
from typing import Any, cast

from normcap.clipboard import system_info

try:
    from PySide6 import QtGui

except ImportError:
    QtGui = cast(Any, None)


logger = logging.getLogger(__name__)

install_instructions = (
    "Please install the Python package PySide6 with your preferred package manager."
)


def copy(text: str) -> None:
    """Use QtWidgets.QApplication.clipboard to copy text to system clipboard."""
    app = QtGui.QGuiApplication.instance() or QtGui.QGuiApplication()

    cb = app.clipboard()  # type: ignore  # Type hint wrong in PySide6?
    cb.setText(text)
    app.processEvents()


def is_compatible() -> bool:
    if not QtGui:
        logger.debug("%s is not compatible on systems w/o PySide6", __name__)
        return False

    if system_info.os_has_wayland_display_manager():
        logger.debug("%s is not compatible with Wayland", __name__)
        return False

    logger.debug("%s is compatible", __name__)
    return True


def is_installed() -> bool:
    logger.debug("%s requires no dependencies", __name__)
    return True
