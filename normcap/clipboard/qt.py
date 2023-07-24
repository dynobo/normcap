from typing import cast

from PySide6 import QtGui


def copy(text: str) -> None:
    """Use QtWidgets.QApplication.clipboard to copy text to system clipboard."""
    app = QtGui.QGuiApplication.instance() or QtGui.QGuiApplication()
    app = cast(QtGui.QGuiApplication, app)

    cb = app.clipboard()
    cb.setText(text)
    app.processEvents()
