"""Helper for clipboard manipulation"""
from normcap.logger import logger


def init():
    """Initialize a wrapper around qt clipboard.

    Necesessary to avoid some wired results on Wayland.
    """
    from PySide2 import QtWidgets  # pylint: disable=import-outside-toplevel

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication()

    def copy_qt(text):
        logger.debug("Copy to clipboard:\n%s", text)
        cb = app.clipboard()
        cb.setText(text)

    return copy_qt
