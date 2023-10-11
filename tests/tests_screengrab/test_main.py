import pytest
from PySide6 import QtGui

from normcap import screengrab
from normcap.screengrab import dbus_portal, dbus_shell, grim, qt, utils


def test_capture():
    # GIVEN any system (with display server)
    # WHEN screenshots are taken
    images = screengrab.capture()

    # THEN we should retrieve at least one image
    assert len(images) > 0
    assert all(isinstance(i, QtGui.QImage) for i in images)


@pytest.mark.parametrize(
    ("sys_platform", "is_wayland", "has_grim", "has_dbus_portal", "expected_func"),
    [
        ("win32", True, True, True, qt.capture),
        ("win32", False, False, False, qt.capture),
        ("darwin", True, True, True, qt.capture),
        ("darwin", False, False, False, qt.capture),
        ("linux", False, True, True, qt.capture),
        ("linux", True, True, True, grim.capture),
        ("linux", True, False, True, dbus_portal.capture),
        ("linux", True, False, False, dbus_shell.capture),
    ],
)
def test_get_capture_func(
    monkeypatch, sys_platform, is_wayland, has_grim, has_dbus_portal, expected_func
):
    monkeypatch.setattr(screengrab.main.sys, "platform", sys_platform)
    monkeypatch.setattr(utils, "has_grim_support", lambda: has_grim)
    monkeypatch.setattr(
        utils, "is_wayland_display_manager", lambda: is_wayland, lambda: is_wayland
    )
    monkeypatch.setattr(
        utils, "has_dbus_portal_support", lambda: has_dbus_portal, lambda: is_wayland
    )

    capture_func = screengrab.main.get_capture_func()

    assert capture_func == expected_func
