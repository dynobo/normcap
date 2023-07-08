import pytest

from normcap import clipboard


@pytest.mark.skipif(
    clipboard.linux._is_wayland_display_manager(), reason="Not applicable on Wayland"
)
def test_copy(qapp):
    text = "test"
    clipboard.qt.copy(text)

    clipboard_content = qapp.clipboard().text()
    assert text == clipboard_content
