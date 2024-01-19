import builtins
import uuid

import pytest

from normcap.clipboard import system_info
from normcap.clipboard.handlers import qtclipboard

real_import = builtins.__import__


@pytest.mark.parametrize(
    ("platform", "wayland_display", "result"),
    [
        ("darwin", "", True),
        ("darwin", "wayland", True),
        ("win32", "", True),
        ("win32", "wayland", True),
        ("linux", "", True),
        ("linux", "wayland", False),
    ],
)
def test_qtclipboard_is_compatible(monkeypatch, platform, wayland_display, result):
    monkeypatch.setenv("WAYLAND_DISPLAY", wayland_display)
    monkeypatch.setenv("XDG_SESSION_TYPE", "")
    monkeypatch.setattr(system_info.sys, "platform", platform)
    assert qtclipboard.is_compatible() == result


def test_qtclipboard_is_compatible_without_pyside6(monkeypatch, mock_import):
    mock_import(parent_module=qtclipboard, import_name="QtGui", throw_exc=ImportError)
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    monkeypatch.setenv("XDG_SESSION_TYPE", "")
    assert qtclipboard.is_compatible() is False


@pytest.mark.skipif(
    system_info.os_has_wayland_display_manager(), reason="non-Wayland specific test"
)
def test_qtclipboard_copy(qapp):
    text = "test"
    qtclipboard.copy(text=text)

    clipped = qapp.clipboard().text()

    assert text == clipped


def test_qtclipboard_copy_fails_on_missing_pyside6(qapp, mock_import):
    text = f"this is a unique test {uuid.uuid4()}"
    mock_import(parent_module=qtclipboard, import_name="QtGui", throw_exc=ImportError)
    with pytest.raises((ImportError, AttributeError)):
        qtclipboard.copy(text=text)

    clipped = qapp.clipboard().text()

    assert text != clipped
