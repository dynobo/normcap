import pytest
from PySide6 import QtGui

from normcap import screenshot
from normcap.screenshot import system_info
from normcap.screenshot.handlers import dbus_portal, gnome_screenshot, grim
from normcap.screenshot.models import Handler


def test_capture(qapp):
    # GIVEN any system (with display server)
    # WHEN screenshots are taken
    images = screenshot.capture()

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
        "has_gnome_screenshot",
        "expected_handler",
    ),
    [
        ("win32", "", False, False, True, False, Handler.QT),
        ("win32", "", False, False, False, False, Handler.QT),
        ("darwin", "", False, False, True, False, Handler.QT),
        ("darwin", "", False, False, False, False, Handler.QT),
        ("linux", "", False, True, True, False, Handler.QT),
        ("linux", "", True, True, True, False, Handler.GRIM),
        ("linux", "", True, False, True, False, Handler.DBUS_PORTAL),
        ("linux", "", True, False, False, False, Handler.DBUS_PORTAL),
        ("linux", "47.0", True, False, False, True, Handler.GNOME_SCREENSHOT),
        ("linux", "42.0", True, False, False, False, Handler.DBUS_PORTAL),
        ("linux", "47.0", True, False, False, False, Handler.DBUS_PORTAL),
        ("linux", "47.0", False, False, False, False, Handler.QT),
        ("linux", "42.0", False, False, False, False, Handler.QT),
        ("linux", "47.0", False, False, True, True, Handler.QT),
    ],
)
def test_get_available_handlers(
    monkeypatch,
    sys_platform,
    gnome_version,
    is_wayland,
    is_wlroots,
    has_grim,
    has_gnome_screenshot,
    expected_handler,
):
    monkeypatch.setattr(screenshot.system_info.sys, "platform", sys_platform)
    monkeypatch.setattr(system_info, "has_wayland_display_manager", lambda: is_wayland)
    monkeypatch.setattr(dbus_portal, "is_installed", lambda: is_wayland)
    monkeypatch.setattr(system_info, "has_wlroots_compositor", lambda: is_wlroots)
    monkeypatch.setattr(system_info, "get_gnome_version", lambda: gnome_version)
    monkeypatch.setattr(system_info, "is_gnome", lambda: bool(gnome_version))

    def _mocked_which(cmd):
        if cmd == "grim" and has_grim:
            return "/usr/bin/grim"
        if cmd == "gnome-screenshot" and has_gnome_screenshot:
            return "/usr/bin/gnome-screenshot"
        return None

    monkeypatch.setattr(grim.shutil, "which", _mocked_which)
    monkeypatch.setattr(gnome_screenshot.shutil, "which", _mocked_which)

    handlers = screenshot.main.get_available_handlers()

    assert handlers[0] == expected_handler, handlers
