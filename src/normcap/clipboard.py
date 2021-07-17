"""Helper for clipboard manipulation"""


def init():
    """Initialize a wrapper around qt clipboard.

    Necesessary to avoid some wired results on Wayland.
    """
    from PySide2 import QtWidgets  # pylint: disable=import-outside-toplevel

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication()

    def copy_qt(text):
        cb = app.clipboard()
        cb.setText(text)

    return copy_qt
