import logging
from typing import Any, cast

from normcap.platform import system_info

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
        return False

    return not system_info.has_wayland_display_manager()


def is_installed() -> bool:
    return True
