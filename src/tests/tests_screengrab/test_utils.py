from decimal import DivisionByZero

from normcap.screengrab import utils


def test_display_manager_is_wayland_on_windows(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "win32")
    is_wayland = utils.display_manager_is_wayland()
    assert is_wayland is False


def test_display_manager_is_wayland_on_linux_xdg_session_type(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "linux")

    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    is_wayland = utils.display_manager_is_wayland()
    assert is_wayland is True

    monkeypatch.setenv("XDG_SESSION_TYPE", "")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    is_wayland = utils.display_manager_is_wayland()
    assert is_wayland is True

    monkeypatch.setenv("XDG_SESSION_TYPE", "gnome-shell")
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    is_wayland = utils.display_manager_is_wayland()
    assert is_wayland is False


def test_gnome_shell_version_on_windows(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "win32")
    version = utils.gnome_shell_version.__wrapped__()
    assert version is None


def test_gnome_shell_version_on_linux(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "linux")

    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "wayland")
    version = utils.gnome_shell_version.__wrapped__()
    assert version is None

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "unity")
    monkeypatch.setattr(
        utils.subprocess, "check_output", lambda *args, **kwargs: b"GNOME Shell 33.3\n"
    )
    version = utils.gnome_shell_version.__wrapped__()
    assert str(version) == "33.3"


def test_gnome_shell_version_on_linux_file_not_found(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "linux")

    def _mocked_subprocess(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "unity")
    monkeypatch.setattr(utils.subprocess, "check_output", _mocked_subprocess)
    version = utils.gnome_shell_version.__wrapped__()
    assert version is None


def test_gnome_shell_version_on_linux_unknown_exception(monkeypatch, caplog):
    monkeypatch.setattr(utils.sys, "platform", "linux")

    def _mocked_subprocess(*args, **kwargs):
        raise DivisionByZero()

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "unity")
    monkeypatch.setattr(utils.subprocess, "check_output", _mocked_subprocess)
    version = utils.gnome_shell_version.__wrapped__()
    assert version is None
    assert "exception when trying to get gnome-shell" in caplog.text.lower()
