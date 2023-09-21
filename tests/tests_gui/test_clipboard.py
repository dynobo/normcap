from normcap import clipboard


def test_copy_to_clipboard(qapp):
    text = "To be copied to system clipboard"
    _copy_to_clipboard = clipboard.get_copy_func()
    _copy_to_clipboard(text)

    clipboard_content = qapp.clipboard().text()
    assert clipboard_content == text
