import builtins
import uuid

import pytest

from normcap.clipboard.handlers import base, qtclipboard
from normcap.clipboard.handlers.base import ClipboardHandlerBase

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
    monkeypatch.setattr(base.sys, "platform", platform)
    assert qtclipboard.QtCopyHandler().is_compatible == result


def test_qtclipboard_is_compatible_without_pyside6(monkeypatch, mock_import):
    mock_import(parent_module=qtclipboard, import_name="QtGui", throw_exc=ImportError)
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    monkeypatch.setenv("XDG_SESSION_TYPE", "")
    assert qtclipboard.QtCopyHandler().is_compatible is False


@pytest.mark.skipif(
    ClipboardHandlerBase._os_has_wayland_display_manager(),
    reason="non-Wayland specific test",
)
def test_qtclipboard_copy(qapp):
    text = "test"
    result = qtclipboard.QtCopyHandler().copy(text=text)

    clipped = qapp.clipboard().text()

    assert result is True
    assert text == clipped


@pytest.mark.skipif(
    not ClipboardHandlerBase._os_has_wayland_display_manager(),
    reason="Wayland specific test",
)
def test_qtclipboard_copy_on_wayland_fails(qapp):
    text = f"this is a unique test {uuid.uuid4()}"

    result = qtclipboard.QtCopyHandler().copy(text=text)
    clipped = qapp.clipboard().text()

    assert clipped is not text
    assert result is False


def test_qtclipboard_copy_fails_on_missing_pyside6(qapp, mock_import):
    text = f"this is a unique test {uuid.uuid4()}"
    mock_import(parent_module=qtclipboard, import_name="QtGui", throw_exc=ImportError)
    result = qtclipboard.QtCopyHandler().copy(text=text)

    clipped = qapp.clipboard().text()

    assert result is False
    assert text != clipped
