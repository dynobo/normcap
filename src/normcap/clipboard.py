"""Helper for clipboard manipulation"""
from normcap.logger import format_section, logger


def init():
    """Initialize a wrapper around qt clipboard.

    Necesessary to avoid some wired results on Wayland.
    """
    from PySide2 import QtWidgets  # pylint: disable=import-outside-toplevel

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication()

    def copy_qt(text):
        logger.debug(f"Copying to clipboard:{format_section(text, title='Clipboard')}")
        cb = app.clipboard()
        cb.setText(text)

    return copy_qt
