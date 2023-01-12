import logging
import os

import pytest

from normcap import clipboard


@pytest.mark.parametrize(
    "wayland_display,xdg_session_type,result",
    [
        ("Wayland", "", True),
        ("", "Gnome Wayland", True),
        ("Wayland", "Gnome Wayland", True),
        ("X11", "Gnome Wayland", True),
        ("X11", "Gnome Shell", False),
    ],
)
def test_is_wayland_display_manager(
    wayland_display, xdg_session_type, result, monkeypatch
):
    def mocked_environ_get(var, default):
        if var == "WAYLAND_DISPLAY":
            return wayland_display
        if var == "XDG_SESSION_TYPE":
            return xdg_session_type
        return os.environ(var, default)

    monkeypatch.setattr(clipboard.linux.os.environ, "get", mocked_environ_get)
    assert clipboard.linux._is_wayland_display_manager() == result


def test_get_copy_func_on_wayland(monkeypatch):
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland")
    monkeypatch.setattr(clipboard.linux.shutil, "which", lambda *args: True)
    get_copy = clipboard.linux.get_copy_func()
    assert get_copy == clipboard.linux._wl_copy


def test_get_copy_func_on_non_wayland(monkeypatch):
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    monkeypatch.setenv("XDG_SESSION_TYPE", "gnome")
    get_copy = clipboard.linux.get_copy_func()
    assert get_copy == clipboard.qt.copy


def test_get_copy_func_on_wayland_without_wl_copy(monkeypatch, caplog):
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland")
    monkeypatch.setattr(clipboard.linux.shutil, "which", lambda *args: None)
    with caplog.at_level(logging.WARNING):
        get_copy = clipboard.linux.get_copy_func()

    assert get_copy == clipboard.qt.copy
    assert "warning" in caplog.text.lower()
    assert "wl-clipboard" in caplog.text.lower()
