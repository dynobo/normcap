import logging
import subprocess
import sys
from decimal import DivisionByZero
from pathlib import Path

import pytest
from PySide6 import QtCore, QtGui, QtWidgets

from normcap.screengrab import dbus_shell, get_capture_func, qt, utils


def test_display_manager_is_wayland_on_windows(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "win32")
    is_wayland = utils.has_wayland_display_manager()
    assert is_wayland is False


def test_display_manager_is_wayland_on_linux_xdg_session_type(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "linux")

    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    is_wayland = utils.has_wayland_display_manager()
    assert is_wayland is True

    monkeypatch.setenv("XDG_SESSION_TYPE", "")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    is_wayland = utils.has_wayland_display_manager()
    assert is_wayland is True

    monkeypatch.setenv("XDG_SESSION_TYPE", "gnome-shell")
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    is_wayland = utils.has_wayland_display_manager()
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
        utils.subprocess, "check_output", lambda *args, **kwargs: "GNOME Shell 33.3\n"
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

    def _mocked_subprocess(*args, **kwargs):
        raise DivisionByZero()

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "gnome")
    monkeypatch.setattr(utils.subprocess, "check_output", _mocked_subprocess)

    version = utils.get_gnome_version()
    assert version is None
    assert "exception when trying to get gnome version" in caplog.text.lower()


@pytest.mark.skipif(sys.platform == "win32", reason="non-Windows specific test")
def test_get_appropriate_capture_on_wayland(monkeypatch):
    from normcap.screengrab import dbus_portal

    monkeypatch.setattr(utils.sys, "platform", "linux")

    monkeypatch.setattr(utils, "has_wayland_display_manager", lambda: True)
    monkeypatch.setattr(utils, "get_gnome_version", lambda: "40.3")
    capture = get_capture_func()
    assert capture == dbus_shell.capture

    monkeypatch.setattr(utils, "has_wayland_display_manager", lambda: True)
    monkeypatch.setattr(utils, "get_gnome_version", lambda: "41.0")
    capture = get_capture_func()
    assert capture == dbus_portal.capture

    monkeypatch.setattr(utils, "has_wayland_display_manager", lambda: True)
    monkeypatch.setattr(utils, "get_gnome_version", lambda: None)
    capture = get_capture_func()
    assert capture == dbus_portal.capture


def test_get_appropriate_capture_on_non_wayland(monkeypatch):
    monkeypatch.setattr(utils, "has_wayland_display_manager", lambda: False)
    monkeypatch.setattr(utils, "get_gnome_version", lambda: None)
    capture = get_capture_func()
    assert capture == qt.capture

    monkeypatch.setattr(utils, "has_wayland_display_manager", lambda: False)
    monkeypatch.setattr(utils, "get_gnome_version", lambda: "41.0")
    grab_screens = get_capture_func()
    assert grab_screens == qt.capture


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS specific test")
def test_macos_has_screenshot_permission(caplog):
    with caplog.at_level(logging.WARNING):
        result = utils._macos_has_screenshot_permission()
    assert isinstance(result, bool)


@pytest.mark.skipif(sys.platform == "darwin", reason="non-macOS specific test")
def test_macos_has_screenshot_permission_on_non_macos(caplog):
    with caplog.at_level(logging.WARNING):
        result = utils._macos_has_screenshot_permission()
    assert "couldn't detect" in caplog.text.lower()
    assert result is True


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS specific test")
def test_macos_request_screenshot_permission(caplog):
    with caplog.at_level(logging.DEBUG):
        utils.macos_request_screenshot_permission()
    assert "request screen recording" in caplog.text.lower()


@pytest.mark.skipif(sys.platform == "darwin", reason="non-macOS specific test")
def test_macos_request_screenshot_permission_on_non_macos(caplog):
    with caplog.at_level(logging.DEBUG):
        utils.macos_request_screenshot_permission()
    assert "couldn't request" in caplog.text.lower()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS specific test")
def test_macos_reset_screenshot_permission(caplog):
    with caplog.at_level(logging.ERROR):
        utils.macos_reset_screenshot_permission()
    assert "couldn't reset" not in caplog.text.lower()


@pytest.mark.skipif(sys.platform == "darwin", reason="non-macOS specific test")
def test_macos_reset_screenshot_permission_on_non_macos(caplog):
    with caplog.at_level(logging.ERROR):
        utils.macos_reset_screenshot_permission()
    assert "couldn't reset" in caplog.text.lower()


def test_macos_reset_screenshot_permission_logs_error(monkeypatch, caplog):
    def mock_failed_cmd(*_, **__):
        return subprocess.CompletedProcess(args="", returncode=1)

    monkeypatch.setattr(utils.subprocess, "run", mock_failed_cmd)
    with caplog.at_level(logging.ERROR):
        utils.macos_reset_screenshot_permission()

    assert "failed resetting screen recording permissions" in caplog.text.lower()


def test_has_screenshot_permission():
    result = utils.has_screenshot_permission()
    assert isinstance(result, bool)


def test_has_screenshot_permission_raises(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "unknown")
    with pytest.raises(RuntimeError, match="Unknown platform"):
        _ = utils.has_screenshot_permission()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS specific test")
def test_macos_open_privacy_settings(caplog):
    with caplog.at_level(logging.ERROR):
        utils.macos_open_privacy_settings()
    assert "couldn't open" not in caplog.text.lower()


@pytest.mark.skipif(sys.platform == "darwin", reason="non-macOS specific test")
def test_macos_open_privacy_settings_on_non_macos(caplog):
    with caplog.at_level(logging.ERROR):
        utils.macos_open_privacy_settings()
    assert "couldn't open" in caplog.text.lower()


def _convert_to_pixels(image):
    image = image.convertToFormat(QtGui.QImage.Format.Format_RGB32)
    ptr = image.constBits()
    values = list(ptr)
    return [tuple(values[i : i + 4]) for i in range(0, len(values), 4)]


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

    monkeypatch.setattr(QtWidgets.QApplication, "primaryScreen", MockedPrimaryScreen)
    monkeypatch.setattr(QtWidgets.QApplication, "screens", mocked_screens)

    img_path = Path(__file__).parent / "split_full_desktop_to_screens.png"
    image = QtGui.QImage()
    image.load(str(img_path.resolve()))
    split_images = utils.split_full_desktop_to_screens(image)

    assert len(split_images) == len(mocked_screens())
    assert {split_images[i].size().toTuple() for i in range(3)} == {(100, 100)}

    assert set(_convert_to_pixels(split_images[0])) == {(0, 0, 255, 255)}
    assert set(_convert_to_pixels(split_images[1])) == {(0, 255, 0, 255)}
    assert set(_convert_to_pixels(split_images[2])) == {(255, 0, 0, 255)}
