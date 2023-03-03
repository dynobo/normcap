import pytest
from PySide6 import QtWidgets

from normcap import clipboard


def test_copy():
    if clipboard.linux._is_wayland_display_manager():
        pytest.xfail("Skip clipboard qt test on Wayland")

    text = "test"
    clipboard.qt.copy(text)

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication()
    cb = app.clipboard()
    clipboard_content = cb.text()
    assert text == clipboard_content
