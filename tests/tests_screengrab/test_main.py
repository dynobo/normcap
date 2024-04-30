import pytest
from PySide6 import QtGui

from normcap import screengrab
from normcap.screengrab import system_info
from normcap.screengrab.handlers import grim
from normcap.screengrab.structures import Handler


def test_capture(qapp):
    # GIVEN any system (with display server)
    # WHEN screenshots are taken
    images = screengrab.capture()

    # THEN we should retrieve at least one image
    assert len(images) > 0
    assert all(isinstance(i, QtGui.QImage) for i in images)


@pytest.mark.parametrize(
    (
        "sys_platform",
        "gnome_version",
        "is_wayland",
        "is_wlroots",
        "has_grim",
        "expected_handler",
    ),
    [
        ("win32", "", True, True, True, Handler.QT),
        ("win32", "", False, False, False, Handler.QT),
        ("darwin", "", True, True, True, Handler.QT),
        ("darwin", "", False, False, False, Handler.QT),
        ("linux", "", False, True, True, Handler.QT),
        ("linux", "", True, True, True, Handler.GRIM),
        ("linux", "", True, False, True, Handler.DBUS_PORTAL),
        ("linux", "", True, False, False, Handler.DBUS_PORTAL),
        ("linux", "41.0", True, False, False, Handler.DBUS_PORTAL),
        ("linux", "41.0", False, False, False, Handler.QT),
        ("linux", "40.0", True, False, False, Handler.DBUS_SHELL),
        ("linux", "40.0", False, False, False, Handler.QT),
    ],
)
def test_get_available_handlers(
    monkeypatch,
    sys_platform,
    gnome_version,
    is_wayland,
    is_wlroots,
    has_grim,
    expected_handler,
):
    monkeypatch.setattr(screengrab.system_info.sys, "platform", sys_platform)
    monkeypatch.setattr(system_info, "has_wayland_display_manager", lambda: is_wayland)
    monkeypatch.setattr(system_info, "has_wlroots_compositor", lambda: is_wlroots)
    monkeypatch.setattr(system_info, "get_gnome_version", lambda: gnome_version)
    monkeypatch.setattr(
        grim.shutil, "which", lambda _: "/usr/bin/grim" if has_grim else None
    )

    handlers = screengrab.main.get_available_handlers()

    assert handlers[0] == expected_handler, handlers
