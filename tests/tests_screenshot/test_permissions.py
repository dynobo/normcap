import logging
import subprocess
import sys

import pytest

from normcap.gui.permissions_dialog import RequestDbusPermissionDialog
from normcap.screenshot import permissions


@pytest.mark.skipif(sys.platform in {"win32", "linux"}, reason="macOS specific test")
def test_macos_has_screenshot_permission(caplog):
    with caplog.at_level(logging.WARNING):
        result = permissions._macos_has_screenshot_permission()
    assert isinstance(result, bool)


class _MockedCoreGraphics:
    """Stand-in for the CoreGraphics library returned by ctypes."""

    def __init__(self, has_screen_capture_access: bool) -> None:
        self.has_screen_capture_access = has_screen_capture_access

    def CGPreflightScreenCaptureAccess(self) -> int:  # noqa: N802 # ctypes API
        return int(self.has_screen_capture_access)


@pytest.mark.skipif(sys.platform == "darwin", reason="non-macOS specific test")
def test_macos_has_screen_capture_access_on_non_macos(caplog):
    with caplog.at_level(logging.WARNING):
        result = permissions._macos_has_screen_capture_access()
    assert "couldn't detect" in caplog.text.lower()
    assert result is True


@pytest.mark.parametrize("has_screen_capture_access", [True, False])
def test_macos_has_screen_capture_access(monkeypatch, has_screen_capture_access):
    monkeypatch.setattr(
        permissions,
        "_macos_load_core_graphics",
        lambda: _MockedCoreGraphics(has_screen_capture_access),
    )
    result = permissions._macos_has_screen_capture_access()
    assert result is has_screen_capture_access


def test_macos_has_screen_capture_access_does_not_reset_permission(monkeypatch):
    monkeypatch.setattr(
        permissions, "_macos_load_core_graphics", lambda: _MockedCoreGraphics(False)
    )
    monkeypatch.setattr(
        permissions,
        "macos_reset_screenshot_permission",
        lambda: pytest.fail("A read-only check must not reset permissions!"),
    )
    assert permissions._macos_has_screen_capture_access() is False


def test_macos_has_screenshot_permission_resets_if_not_granted(monkeypatch):
    monkeypatch.setattr(
        permissions, "_macos_load_core_graphics", lambda: _MockedCoreGraphics(False)
    )
    reset_calls = []
    monkeypatch.setattr(
        permissions,
        "macos_reset_screenshot_permission",
        lambda: reset_calls.append(True),
    )
    assert permissions._macos_has_screenshot_permission() is False
    assert reset_calls


@pytest.mark.skipif(sys.platform == "darwin", reason="non-macOS specific test")
def test_macos_has_screenshot_permission_on_non_macos(caplog):
    with caplog.at_level(logging.WARNING):
        result = permissions._macos_has_screenshot_permission()
    assert "couldn't detect" in caplog.text.lower()
    assert result is True


@pytest.mark.skipif(sys.platform in {"win32", "linux"}, reason="macOS specific test")
def test_macos_request_screenshot_permission(caplog):
    with caplog.at_level(logging.DEBUG):
        permissions.macos_request_screenshot_permission()
    assert "request screen recording" in caplog.text.lower()


@pytest.mark.skipif(sys.platform == "darwin", reason="non-macOS specific test")
def test_macos_request_screenshot_permission_on_non_macos(caplog):
    with caplog.at_level(logging.DEBUG):
        permissions.macos_request_screenshot_permission()
    assert "couldn't request" in caplog.text.lower()


@pytest.mark.skipif(sys.platform in {"win32", "linux"}, reason="macOS specific test")
def test_macos_reset_screenshot_permission(caplog):
    with caplog.at_level(logging.ERROR):
        permissions.macos_reset_screenshot_permission()
    assert "couldn't reset" not in caplog.text.lower()


@pytest.mark.skipif(sys.platform == "darwin", reason="non-macOS specific test")
def test_macos_reset_screenshot_permission_on_non_macos(caplog):
    with caplog.at_level(logging.ERROR):
        permissions.macos_reset_screenshot_permission()
    assert "couldn't reset" in caplog.text.lower()


def test_macos_reset_screenshot_permission_logs_error(monkeypatch, caplog):
    def mock_failed_cmd(*_, **__):
        return subprocess.CompletedProcess(args="", returncode=1)

    monkeypatch.setattr(permissions.subprocess, "run", mock_failed_cmd)
    with caplog.at_level(logging.ERROR):
        permissions.macos_reset_screenshot_permission()

    assert "failed resetting screen recording permissions" in caplog.text.lower()


def test_has_screenshot_permission(qapp):
    result = permissions.has_screenshot_permission(
        request_portal_dialog=RequestDbusPermissionDialog(capture_func=lambda: ...)
    )
    assert isinstance(result, bool)


@pytest.mark.skipif(sys.platform != "linux", reason="linux specific test")
def test_has_screenshot_permission_raises(monkeypatch, qapp):
    monkeypatch.setattr(permissions, "get_available_handlers", lambda: [])
    with pytest.raises(RuntimeError, match="screenshot method"):
        _ = permissions.has_screenshot_permission(
            request_portal_dialog=RequestDbusPermissionDialog(capture_func=lambda: ...)
        )


@pytest.mark.skipif(sys.platform in {"win32", "linux"}, reason="macOS specific test")
def test_macos_open_privacy_settings(caplog):
    with caplog.at_level(logging.ERROR):
        permissions._macos_open_privacy_settings()
    assert "couldn't open" not in caplog.text.lower()


@pytest.mark.skipif(sys.platform in {"win32", "linux"}, reason="macOS specific test")
def test_macos_open_privacy_settings_logs_exception(monkeypatch, caplog):
    def mocked_run(*_, **__):
        raise ValueError("Mocked exception on 'open' call")

    monkeypatch.setattr(subprocess, "run", mocked_run)
    with caplog.at_level(logging.ERROR):
        permissions._macos_open_privacy_settings()
    assert "couldn't open" in caplog.text.lower()


@pytest.mark.skipif(sys.platform == "darwin", reason="non-macOS specific test")
def test_macos_open_privacy_settings_on_non_macos(caplog):
    with caplog.at_level(logging.ERROR):
        permissions._macos_open_privacy_settings()
    assert "couldn't open" in caplog.text.lower()
