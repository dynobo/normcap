from decimal import DivisionByZero

from packaging.version import Version

from normcap.screengrab import (
    _get_appropriate_capture,
    dbus_portal,
    dbus_shell,
    qt,
    utils,
)


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
    version = utils.get_gnome_version.__wrapped__()
    assert version is None


def test_gnome_version_on_linux_from_cmd(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "linux")

    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "wayland")
    version = utils.get_gnome_version.__wrapped__()
    assert version is None

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "unity")
    monkeypatch.setattr(utils, "_get_gnome_version_xml", lambda *args, **kwargs: 1 / 0)
    monkeypatch.setattr(
        utils.subprocess, "check_output", lambda *args, **kwargs: b"GNOME Shell 33.3\n"
    )
    version = utils.get_gnome_version.__wrapped__()
    assert str(version) == "33.3"


def test_gnome_version_on_linux_from_xml(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "linux")

    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "wayland")
    version = utils.get_gnome_version.__wrapped__()
    assert version is None

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "unity")
    monkeypatch.setattr(
        utils,
        "_get_gnome_version_xml",
        lambda: '<?xml version="1.0"?>\n<gnome-version>\n<platform>22</platform>\n'
        + "<minor>2</minor>\n<micro>0</micro>\n<distributor>Arch Linux</distributor>\n"
        + "<!--<date></date>-->\n</gnome-version>",
    )
    monkeypatch.setattr(
        utils.subprocess, "check_output", lambda *args, **kwargs: b"GNOME Shell 33.3\n"
    )
    version = utils.get_gnome_version.__wrapped__()
    assert str(version) == "22.2"


def test_gnome_version_on_linux_file_not_found(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "linux")

    def _mocked_subprocess(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "unity")
    monkeypatch.setattr(utils.subprocess, "check_output", _mocked_subprocess)
    monkeypatch.setattr(utils, "_get_gnome_version_xml", lambda *args, **kwargs: 1 / 0)

    version = utils.get_gnome_version.__wrapped__()
    assert version is None


def test_gnome_version_on_linux_unknown_exception(monkeypatch, caplog):
    monkeypatch.setattr(utils.sys, "platform", "linux")

    def _mocked_subprocess(*args, **kwargs):
        raise DivisionByZero()

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "unity")
    monkeypatch.setattr(utils.subprocess, "check_output", _mocked_subprocess)
    monkeypatch.setattr(utils, "_get_gnome_version_xml", lambda *args, **kwargs: 1 / 0)

    version = utils.get_gnome_version.__wrapped__()
    assert version is None
    assert "exception when trying to get gnome version" in caplog.text.lower()


def test_get_appropriate_capture_on_wayland(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "linux")

    monkeypatch.setattr(utils, "has_wayland_display_manager", lambda: True)
    monkeypatch.setattr(utils, "get_gnome_version", lambda: Version("40.3"))
    capture = _get_appropriate_capture()
    assert capture == dbus_shell.capture

    monkeypatch.setattr(utils, "has_wayland_display_manager", lambda: True)
    monkeypatch.setattr(utils, "get_gnome_version", lambda: Version("41.0"))
    capture = _get_appropriate_capture()
    assert capture == dbus_portal.capture

    monkeypatch.setattr(utils, "has_wayland_display_manager", lambda: True)
    monkeypatch.setattr(utils, "get_gnome_version", lambda: None)
    capture = _get_appropriate_capture()
    assert capture == dbus_portal.capture


def test_get_appropriate_capture_on_non_wayland(monkeypatch):
    monkeypatch.setattr(utils, "has_wayland_display_manager", lambda: False)
    monkeypatch.setattr(utils, "get_gnome_version", lambda: None)
    capture = _get_appropriate_capture()
    assert capture == qt.capture

    monkeypatch.setattr(utils, "has_wayland_display_manager", lambda: False)
    monkeypatch.setattr(utils, "get_gnome_version", lambda: Version("41.0"))
    grab_screens = _get_appropriate_capture()
    assert grab_screens == qt.capture
