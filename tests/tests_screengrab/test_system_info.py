from decimal import DivisionByZero

from normcap.screengrab import system_info


# TODO: Parametrize tests?
def test_display_manager_is_wayland_on_windows(monkeypatch):
    monkeypatch.setattr(system_info.sys, "platform", "win32")
    is_wayland = system_info.has_wayland_display_manager()
    assert is_wayland is False


def test_display_manager_is_wayland_on_linux_xdg_session_type(monkeypatch):
    monkeypatch.setattr(system_info.sys, "platform", "linux")

    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    is_wayland = system_info.has_wayland_display_manager()
    assert is_wayland is True

    monkeypatch.setenv("XDG_SESSION_TYPE", "")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    is_wayland = system_info.has_wayland_display_manager()
    assert is_wayland is True

    monkeypatch.setenv("XDG_SESSION_TYPE", "gnome-shell")
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    is_wayland = system_info.has_wayland_display_manager()
    assert is_wayland is False


def test_gnome_version_on_windows(monkeypatch):
    monkeypatch.setattr(system_info.sys, "platform", "win32")
    version = system_info.get_gnome_version()
    assert not version


def test_gnome_version_on_linux_from_cmd(monkeypatch):
    monkeypatch.setattr(system_info.sys, "platform", "linux")
    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "wayland")
    monkeypatch.setattr(system_info.shutil, "which", lambda _: True)
    system_info.get_gnome_version.cache_clear()
    version = system_info.get_gnome_version()
    assert not version

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "gnome")
    monkeypatch.setattr(
        system_info.subprocess,
        "check_output",
        lambda *args, **kwargs: "GNOME Shell 33.3\n",
    )
    system_info.get_gnome_version.cache_clear()
    version = system_info.get_gnome_version()
    assert str(version) == "33.3"


def test_gnome_version_on_linux_without_gnome_shell(monkeypatch):
    monkeypatch.setattr(system_info.sys, "platform", "linux")
    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "unity")
    system_info.get_gnome_version.cache_clear()
    version = system_info.get_gnome_version()
    assert not version

    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "some-id")
    monkeypatch.setattr(system_info.shutil, "which", lambda _: False)
    system_info.get_gnome_version.cache_clear()
    version = system_info.get_gnome_version()
    assert not version


def test_gnome_version_on_linux_unknown_exception(monkeypatch, caplog):
    monkeypatch.setattr(system_info.sys, "platform", "linux")
    monkeypatch.setattr(system_info.shutil, "which", lambda _: True)

    def mocked_subprocess(*args, **kwargs):
        raise DivisionByZero()

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "gnome")
    monkeypatch.setattr(system_info.subprocess, "check_output", mocked_subprocess)

    version = system_info.get_gnome_version()
    assert not version
    assert "exception when trying to get gnome version" in caplog.text.lower()
