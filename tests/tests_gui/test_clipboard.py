import sys

from PySide6 import QtGui

from normcap import clipboard


def test_copy_to_clipboard():
    if sys.platform.lower() == "linux":
        return

    text = "To be copied to system clipboard"
    _copy_to_clipboard = clipboard.get_copy_func()
    _copy_to_clipboard(text)

    read_from_clipboard = QtGui.QGuiApplication.clipboard()
    text_from_clipboard = read_from_clipboard.text()

    assert text_from_clipboard == text
