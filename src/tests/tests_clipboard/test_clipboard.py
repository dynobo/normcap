import pytest
from normcap import clipboard


def test_get_copy_func_on_win32(monkeypatch):
    monkeypatch.setattr(clipboard.sys, "platform", "win32")
    get_copy = clipboard.get_copy_func()
    assert get_copy == clipboard.windows.get_copy_func()


def test_get_copy_func_on_darwin(monkeypatch):
    monkeypatch.setattr(clipboard.sys, "platform", "darwin")
    get_copy = clipboard.get_copy_func()
    assert get_copy == clipboard.macos.get_copy_func()


def test_get_copy_func_on_linux(monkeypatch):
    monkeypatch.setattr(clipboard.sys, "platform", "linux")
    get_copy = clipboard.get_copy_func()
    assert get_copy == clipboard.linux.get_copy_func()


def test_get_copy_func_on_unknown(monkeypatch):
    monkeypatch.setattr(clipboard.sys, "platform", "cygwin")
    with pytest.raises(RuntimeError, match="Unknown platform"):
        _ = clipboard.get_copy_func()
