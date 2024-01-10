from normcap import clipboard


def test_copy():
    # GIVEN any platform (and xclip or wl-clipboard for wayland)
    # WHEN text is copied to the clipboard
    result = clipboard.copy(text="this is a test")

    # THEN we expect a working clipboard handler should be selected and run
    assert result is True


def test_copy_without_compatible_handler_fails(monkeypatch):
    # GIVEN a system is mocked to not supported any implemented clipboard handler
    for handler in clipboard.ClipboardHandlers:
        monkeypatch.setattr(
            clipboard.ClipboardHandlers[handler.name].value,
            "is_compatible",
            lambda: False,
        )

    # WHEN text is copied to the clipboard
    result = clipboard.copy(text="this is a test")

    # THEN we expect an unsuccessful return value
    assert result is False
