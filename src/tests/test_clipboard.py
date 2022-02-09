import pytest
from PySide2 import QtGui

from normcap import clipboard


@pytest.mark.skip_on_gh_linux
def test_init_clipboard():
    """Test if clipboard wrapper works correctely."""
    text = "To be copied to system clipboard"
    _copy_to_clipboard = clipboard.init()
    _copy_to_clipboard(text)

    read_from_clipboard = QtGui.QGuiApplication.clipboard()
    text_from_clipboard = read_from_clipboard.text()

    assert text_from_clipboard == text
