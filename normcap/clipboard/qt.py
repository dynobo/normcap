from PySide6 import QtWidgets


def copy(text: str) -> None:
    """Use QtWidgets.QApplication.clipboard to copy text to system clipboard."""
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication()
    cb = app.clipboard()
    cb.setText(text)
    app.processEvents()
