import shutil

import pytest

from normcap import clipboard


def test_copy():
    # GIVEN any platform (and xclip or wl-clipboard for wayland)
    # WHEN text is copied to the clipboard
    result = clipboard.copy(text="this is a test")

    # THEN we expect a working clipboard handler should be selected and run
    assert result is True


def test_copy_without_compatible_handler_fails(monkeypatch):
    # GIVEN a system is mocked to not supported any implemented clipboard handler
    for handler in clipboard.main._clipboard_handlers.values():
        monkeypatch.setattr(handler, "is_compatible", lambda: False)

    # WHEN text is copied to the clipboard
    result = clipboard.copy(text="this is a test")

    # THEN we expect an unsuccessful return value
    assert result is False


@pytest.mark.skipif(
    clipboard.system_info.os_has_wayland_display_manager()
    and not (shutil.which("wl-copy") or shutil.which("xclip")),
    reason="Needs wl-cop or xclip",
)
def test_get_available_handlers():
    # GIVEN a system with at least one compatible and installed clipboard handler
    # WHEN we call get_available_handlers
    available_handlers = clipboard.main.get_available_handlers()

    # THEN we expect at least one handler to be available
    assert available_handlers
