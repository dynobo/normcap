from normcap.clipboard import main


def test_copy():
    # GIVEN any platform (and xclip or wl-clipboard for wayland)
    # WHEN text is copied to the clipboard
    result = main.copy(text="this is a test")

    # THEN we expect a working clipboard handler should be selected and run
    assert result is True


def test_copy_without_compatible_handler_fails(monkeypatch):
    # GIVEN a system is mocked to not supported any implemented clipboard handler
    for handler in main.clipboard_handlers:
        monkeypatch.setattr(handler, "_is_compatible", lambda *args: False)

    # WHEN text is copied to the clipboard
    result = main.copy(text="this is a test")

    # THEN we expect an unsuccessful return value
    assert result is False


def test_has_compatible_strategy():
    # GIVEN any platform (and xclip or wl-clipboard for wayland)
    # WHEN we check for a compatible handler
    system_is_supported = main.has_compatible_handler()

    # THEN we expect to find a compatible handler
    assert system_is_supported is True


def test_get_compatible_strategies():
    # GIVEN any platform (and xclip or wl-clipboard for wayland)
    # WHEN we query compatible handlers
    strategies = main.get_compatible_handlers()

    # THEN we expect to find at least one and all should really be compatible
    assert len(strategies) > 0
    assert all(s.is_compatible for s in strategies)
