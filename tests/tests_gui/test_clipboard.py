import sys

import pytest

from normcap import clipboard


# TODO: Check if this test doesn't run on other platforms
@pytest.mark.skipif(sys.platform == "linux", reason="Linux specific test?")
def test_copy_to_clipboard(qapp):
    text = "To be copied to system clipboard"
    _copy_to_clipboard = clipboard.get_copy_func()
    _copy_to_clipboard(text)

    clipboard_content = qapp.clipboard().text()
    assert clipboard_content == text
