import subprocess
import sys
from decimal import DivisionByZero
from pathlib import Path

import pytest
from PySide6 import QtCore, QtGui, QtWidgets

from normcap.screengrab import dbus_shell, qt, utils
from normcap.screengrab.main import get_capture_func


def test_display_manager_is_wayland_on_windows(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "win32")
    is_wayland = utils.is_wayland_display_manager()
    assert is_wayland is False


def test_display_manager_is_wayland_on_linux_xdg_session_type(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "linux")

    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    is_wayland = utils.is_wayland_display_manager()
    assert is_wayland is True

    monkeypatch.setenv("XDG_SESSION_TYPE", "")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    is_wayland = utils.is_wayland_display_manager()
    assert is_wayland is True

    monkeypatch.setenv("XDG_SESSION_TYPE", "gnome-shell")
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    is_wayland = utils.is_wayland_display_manager()
    assert is_wayland is False


def test_gnome_version_on_windows(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "win32")
    version = utils.get_gnome_version()
    assert version is None


def test_gnome_version_on_linux_from_cmd(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "linux")
    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "wayland")
    monkeypatch.setattr(utils.shutil, "which", lambda _: True)
    utils.get_gnome_version.cache_clear()
    version = utils.get_gnome_version()
    assert version is None

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "gnome")
    monkeypatch.setattr(
        utils.subprocess,
        "check_output",
        lambda *args, **kwargs: "GNOME Shell 33.3\n",
    )
    utils.get_gnome_version.cache_clear()
    version = utils.get_gnome_version()
    assert str(version) == "33.3"


def test_gnome_version_on_linux_without_gnome_shell(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "linux")
    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "unity")
    utils.get_gnome_version.cache_clear()
    version = utils.get_gnome_version()
    assert version is None

    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "some-id")
    monkeypatch.setattr(utils.shutil, "which", lambda _: False)
    utils.get_gnome_version.cache_clear()
    version = utils.get_gnome_version()
    assert version is None


def test_gnome_version_on_linux_unknown_exception(monkeypatch, caplog):
    monkeypatch.setattr(utils.sys, "platform", "linux")
    monkeypatch.setattr(utils.shutil, "which", lambda _: True)

    def mocked_subprocess(*args, **kwargs):
        raise DivisionByZero()

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "gnome")
    monkeypatch.setattr(utils.subprocess, "check_output", mocked_subprocess)

    version = utils.get_gnome_version()
    assert version is None
    assert "exception when trying to get gnome version" in caplog.text.lower()


@pytest.mark.skipif(sys.platform == "win32", reason="non-Windows specific test")
def test_get_appropriate_capture_on_wayland(monkeypatch):
    from normcap.screengrab import dbus_portal

    monkeypatch.setattr(utils.sys, "platform", "linux")

    monkeypatch.setattr(utils, "is_wayland_display_manager", lambda: True)
    monkeypatch.setattr(utils, "get_gnome_version", lambda: "40.3")
    capture = get_capture_func()
    assert capture == dbus_shell.capture

    monkeypatch.setattr(utils, "is_wayland_display_manager", lambda: True)
    monkeypatch.setattr(utils, "get_gnome_version", lambda: "41.0")
    capture = get_capture_func()
    assert capture == dbus_portal.capture

    monkeypatch.setattr(utils, "is_wayland_display_manager", lambda: True)
    monkeypatch.setattr(utils, "get_gnome_version", lambda: None)
    capture = get_capture_func()
    assert capture == dbus_portal.capture


def test_get_appropriate_capture_on_non_wayland(monkeypatch):
    monkeypatch.setattr(utils, "is_wayland_display_manager", lambda: False)
    monkeypatch.setattr(utils, "get_gnome_version", lambda: None)
    capture = get_capture_func()
    assert capture == qt.capture

    monkeypatch.setattr(utils, "is_wayland_display_manager", lambda: False)
    monkeypatch.setattr(utils, "get_gnome_version", lambda: "41.0")
    grab_screens = get_capture_func()
    assert grab_screens == qt.capture


def test_has_grim_support(monkeypatch):
    # GIVEN a system with workable grim (or a mocked one)
    if not utils.shutil.which("grim"):
        monkeypatch.setattr(utils.shutil, "which", lambda _: "/usr/bin/grim")
    try:
        subprocess.run(["grim", "test.png"], check=True)  # noqa: S603, S607
    except:  # noqa: E722
        monkeypatch.setattr(
            utils.subprocess,
            "run",
            lambda *_, **__: subprocess.CompletedProcess(args="", returncode=0),
        )

    # WHEN the function is called
    has_grim = utils.has_grim_support()

    # THEN the grim support should indicated
    assert has_grim


def test_has_grim_support_no_grim_binary(monkeypatch):
    # GIVEN a system without grim binary (or mocked away)
    if utils.shutil.which("grim"):
        monkeypatch.setattr(utils.shutil, "which", lambda _: None)

    # WHEN the function is called
    has_grim = utils.has_grim_support()

    # THEN the no grim support should indicated
    assert not has_grim


def test_has_grim_support_raises_on_grim_call(monkeypatch, caplog):
    # GIVEN a system with workable grim
    #    and a (mocked) Exception is raised on its execution
    if not utils.shutil.which("grim"):
        monkeypatch.setattr(utils.shutil, "which", lambda _: "/usr/bin/grim")

    def mocked_subprocess_run(*_, **__):
        raise OSError

    monkeypatch.setattr(utils.subprocess, "run", mocked_subprocess_run)

    # WHEN the function is called
    has_grim = utils.has_grim_support()

    # THEN then no grim support should indicated
    #    and an error should be logged
    assert not has_grim
    assert "error" in caplog.text.lower()
    assert "grim support" in caplog.text


def test_split_full_desktop_to_screens(monkeypatch):
    class MockedPrimaryScreen:
        def virtualGeometry(self) -> QtCore.QRect:  # noqa: N802
            return QtCore.QRect(0, 0, 300, 120)

    class MockedScreen:
        def __init__(self, left, top, width, height):
            self._geometry = QtCore.QRect(left, top, width, height)

        def geometry(self):
            return self._geometry

    def mocked_screens() -> list:
        return [
            MockedScreen(0, 0, 100, 100),
            MockedScreen(100, 10, 100, 100),
            MockedScreen(200, 20, 100, 100),
        ]

    def convert_to_pixels(image):
        image = image.convertToFormat(QtGui.QImage.Format.Format_RGB32)
        ptr = image.constBits()
        values = list(ptr)
        return [tuple(values[i : i + 4]) for i in range(0, len(values), 4)]

    monkeypatch.setattr(QtWidgets.QApplication, "primaryScreen", MockedPrimaryScreen)
    monkeypatch.setattr(QtWidgets.QApplication, "screens", mocked_screens)

    img_path = Path(__file__).parent / "split_full_desktop_to_screens.png"
    image = QtGui.QImage()
    image.load(str(img_path.resolve()))
    split_images = utils.split_full_desktop_to_screens(image)

    assert len(split_images) == len(mocked_screens())
    assert {split_images[i].size().toTuple() for i in range(3)} == {(100, 100)}

    assert set(convert_to_pixels(split_images[0])) == {(0, 0, 255, 255)}
    assert set(convert_to_pixels(split_images[1])) == {(0, 255, 0, 255)}
    assert set(convert_to_pixels(split_images[2])) == {(255, 0, 0, 255)}
