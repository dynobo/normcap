import logging
import subprocess
import sys

import pytest

from normcap.screengrab import permissions


@pytest.mark.skipif(sys.platform in {"win32", "linux"}, reason="macOS specific test")
def test_macos_has_screenshot_permission(caplog):
    with caplog.at_level(logging.WARNING):
        result = permissions._macos_has_screenshot_permission()
    assert isinstance(result, bool)


@pytest.mark.skipif(sys.platform == "darwin", reason="non-macOS specific test")
def test_macos_has_screenshot_permission_on_non_macos(caplog):
    with caplog.at_level(logging.WARNING):
        result = permissions._macos_has_screenshot_permission()
    assert "couldn't detect" in caplog.text.lower()
    assert result is True


@pytest.mark.skipif(sys.platform in {"win32", "linux"}, reason="macOS specific test")
def test_macos_request_screenshot_permission(caplog):
    with caplog.at_level(logging.DEBUG):
        permissions._macos_request_screenshot_permission()
    assert "request screen recording" in caplog.text.lower()


@pytest.mark.skipif(sys.platform == "darwin", reason="non-macOS specific test")
def test_macos_request_screenshot_permission_on_non_macos(caplog):
    with caplog.at_level(logging.DEBUG):
        permissions._macos_request_screenshot_permission()
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
    result = permissions.has_screenshot_permission()
    assert isinstance(result, bool)


def test_has_screenshot_permission_raises(monkeypatch, qapp):
    monkeypatch.setattr(permissions.sys, "platform", "unknown")
    with pytest.raises(NotImplementedError, match="for this platform"):
        _ = permissions.has_screenshot_permission()


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
