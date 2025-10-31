import logging
import sys
from decimal import DivisionByZero
from pathlib import Path

import pytest

from normcap.system import info
from normcap.system.models import DesktopEnvironment, Screen


def test_display_manager_is_wayland(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland")
    info.display_manager_is_wayland.cache_clear()
    assert info.display_manager_is_wayland()

    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    info.display_manager_is_wayland.cache_clear()
    assert info.display_manager_is_wayland()


def test_display_manager_is_not_wayland(monkeypatch):
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    info.display_manager_is_wayland.cache_clear()
    assert not info.display_manager_is_wayland()

    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    monkeypatch.setenv("XDG_SESSION_TYPE", "something")
    info.display_manager_is_wayland.cache_clear()
    assert not info.display_manager_is_wayland()


def test_desktop_environment():
    assert info.desktop_environment() in DesktopEnvironment


@pytest.mark.parametrize(
    ("envs", "expected_environment"),
    [
        (
            {
                "GNOME_DESKTOP_SESSION_ID": "this-is-deprecated",
                "XDG_CURRENT_DESKTOP": "gnome",
            },
            DesktopEnvironment.GNOME,
        ),
        ({"GNOME_DESKTOP_SESSION_ID": "1"}, DesktopEnvironment.GNOME),
        ({"XDG_CURRENT_DESKTOP": "gnome"}, DesktopEnvironment.GNOME),
        ({"KDE_FULL_SESSION": "1"}, DesktopEnvironment.KDE),
        ({"DESKTOP_SESSION": "kde-plasma"}, DesktopEnvironment.KDE),
        ({"XDG_CURRENT_DESKTOP": "sway"}, DesktopEnvironment.SWAY),
        ({"XDG_CURRENT_DESKTOP": "unity"}, DesktopEnvironment.UNITY),
        ({"HYPRLAND_INSTANCE_SIGNATURE": "something"}, DesktopEnvironment.HYPRLAND),
        ({}, DesktopEnvironment.OTHER),
    ],
)
def test_desktop_environment_gnome(monkeypatch, envs, expected_environment):
    # GIVEN a certain set of environment variables have certain values
    info.desktop_environment.cache_clear()
    env_vars = [
        "GNOME_DESKTOP_SESSION_ID",
        "KDE_FULL_SESSION",
        "DESKTOP_SESSION",
        "XDG_CURRENT_DESKTOP",
        "HYPRLAND_INSTANCE_SIGNATURE",
    ]
    for var in env_vars:
        monkeypatch.setenv(var, envs.get(var, ""))

    # WHEN we try to identify the desktop environment
    environment = info.desktop_environment()

    # THEN it should be the one matching the environment variable
    assert environment == expected_environment


def test_is_briefcase_package():
    assert not info.is_briefcase_package()
    info.is_briefcase_package.cache_clear()

    temp_app_packages = Path(__file__).resolve().parents[3] / "app_packages"
    is_briefcase = False
    try:
        temp_app_packages.mkdir()
        is_briefcase = info.is_briefcase_package()
    finally:
        temp_app_packages.rmdir()

    assert is_briefcase


def test_is_flatpak(monkeypatch):
    assert not info.is_flatpak()
    info.is_flatpak.cache_clear()

    with monkeypatch.context() as m:
        m.setattr(sys, "platform", "linux")
        m.setenv("FLATPAK_ID", "123")
        assert info.is_flatpak()


def test_screens(qtbot):
    screens = info.screens()
    assert len(screens) >= 1
    assert all(isinstance(s, Screen) for s in screens)
    assert isinstance(screens[0], Screen)
    assert isinstance(screens[0].width, int)
    assert isinstance(screens[0].height, int)


def test_config_directory_on_windows(monkeypatch, tmp_path):
    with monkeypatch.context() as m:
        m.setattr(sys, "platform", "win32")
        m.setenv("LOCALAPPDATA", str(tmp_path.absolute()))
        info.config_directory.cache_clear()
        assert info.config_directory() == tmp_path / "normcap"

        m.setenv("LOCALAPPDATA", "")
        m.setenv("APPDATA", str(tmp_path.absolute()))
        info.config_directory.cache_clear()
        assert info.config_directory() == tmp_path / "normcap"

        m.setenv("LOCALAPPDATA", "")
        m.setenv("APPDATA", "")
        info.config_directory.cache_clear()
        with pytest.raises(ValueError, match="Could not determine the appdata"):
            _ = info.config_directory()


def test_config_directory_on_linux_macos(monkeypatch, tmp_path):
    with monkeypatch.context() as m:
        m.setattr(sys, "platform", "linux")
        m.setenv("XDG_CONFIG_HOME", str(tmp_path.absolute()))
        config_dir = info.config_directory()
    assert config_dir == tmp_path / "normcap"


def test_config_directory_fallback(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(sys, "platform", "unknown")
        m.delenv("XDG_CONFIG_HOME", raising=False)
        config_dir = info.config_directory()
    assert config_dir.name == "normcap"
    assert config_dir.parent.name == ".config"


def test_to_dict():
    string = info.to_dict()
    expected = [
        "cli_args",
        "is_briefcase_package",
        "is_flatpak_package",
        "platform",
        "pyside6_version",
        "qt_version",
        "qt_library_path",
        "config_directory",
        "normcap_version",
        "tesseract_path",
        "tessdata_path",
        "envs",
        "desktop_environment",
        "display_manager_is_wayland",
        "screens",
    ]
    for item in expected:
        assert item in string


@pytest.mark.parametrize(
    ("platform", "binary", "directory"),
    [
        ("linux", "tesseract", "bin"),
        ("win32", "tesseract.exe", "tesseract"),
        ("darwin", "tesseract", "bin"),
    ],
)
def test_get_tesseract_path_in_briefcase(monkeypatch, platform, binary, directory):
    with monkeypatch.context() as m:
        m.setattr(info, "is_briefcase_package", lambda: True)
        m.setattr(info.Path, "exists", lambda *args: True)
        m.setattr(info.sys, "platform", platform)
        path = info.get_tesseract_bin_path(
            is_briefcase_package=info.is_briefcase_package()
        )
    assert path.name == binary
    assert path.parent.name == directory


def test_get_tesseract_path_unknown_platform_raises(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(info, "is_briefcase_package", lambda: True)
        m.setattr(info.Path, "exists", lambda *args: True)
        m.setattr(info.sys, "platform", "unknown")
        with pytest.raises(ValueError, match="Platform unknown is not supported"):
            _ = info.get_tesseract_bin_path(
                is_briefcase_package=info.is_briefcase_package()
            )


def test_get_tesseract_path_missing_binary_raises(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(info, "is_briefcase_package", lambda: True)
        with pytest.raises(RuntimeError, match="Could not locate Tesseract binary"):
            _ = info.get_tesseract_bin_path(
                is_briefcase_package=info.is_briefcase_package()
            )


def test_get_tesseract_path_missing_tesseract_raises(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(info.shutil, "which", lambda _: False)
        with pytest.raises(RuntimeError, match="No Tesseract binary found"):
            _ = info.get_tesseract_bin_path(
                is_briefcase_package=info.is_briefcase_package()
            )


@pytest.mark.parametrize(
    ("is_briefcase", "is_flatpak", "has_prefix", "expected_path_end"),
    [
        (True, False, False, "tessdata"),
        (False, True, False, "tessdata"),
        (False, False, True, "tessdata"),
        (False, False, False, None),
    ],
)
def test_get_tessdata_path(
    monkeypatch, caplog, is_briefcase, is_flatpak, has_prefix, expected_path_end
):
    data_file = info.config_directory() / "tessdata" / "mocked.traineddata"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.touch(exist_ok=True)

    try:
        with monkeypatch.context() as m:
            m.setattr(info, "is_briefcase_package", lambda: is_briefcase)
            m.setattr(info, "is_flatpak", lambda: is_flatpak)
            if has_prefix:
                m.setenv("TESSDATA_PREFIX", f"{data_file.resolve().parents[1]}")

            path_briefcase = info.get_tessdata_path(
                config_directory=info.config_directory(),
                is_packaged=info.is_packaged(),
            )

            path_end = (
                str(path_briefcase)[-len("tessdata") :] if path_briefcase else None
            )
            assert path_end == expected_path_end

    finally:
        data_file.unlink()


def test_get_tessdata_path_warn_on_win32(monkeypatch, caplog):
    data_file = info.config_directory() / "tessdata" / "mocked.traineddata"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.touch(exist_ok=True)

    try:
        with monkeypatch.context() as m:
            m.setattr(info, "is_briefcase_package", lambda: False)
            m.setattr(info, "is_flatpak", lambda: False)
            m.setenv("TESSDATA_PREFIX", "")

            monkeypatch.setattr(info.sys, "platform", "win32")
            with caplog.at_level(logging.WARNING):
                caplog.clear()
                _ = info.get_tessdata_path(
                    config_directory=info.config_directory(),
                    is_packaged=info.is_packaged(),
                )
            assert "TESSDATA_PREFIX" in caplog.records[0].msg

    finally:
        data_file.unlink()


@pytest.mark.parametrize(
    ("xdg_session_type", "wayland_display", "platform", "expected_result"),
    [
        ("wayland", "wayland", "linux", True),
        ("wayland", "", "linux", True),
        ("", "wayland", "linux", True),
        ("", "", "linux", False),
        ("wayland", "wayland", "win32", False),
        ("wayland", "wayland", "darwin", False),
    ],
)
def test_os_has_wayland_display_manager(
    monkeypatch, xdg_session_type, wayland_display, platform, expected_result
):
    monkeypatch.setenv("XDG_SESSION_TYPE", xdg_session_type)
    monkeypatch.setenv("WAYLAND_DISPLAY", wayland_display)
    monkeypatch.setattr(info.sys, "platform", platform)

    assert info.has_wayland_display_manager() == expected_result


@pytest.mark.parametrize(
    ("platform", "desktop", "expected_result"),
    [
        ("linux", "awesome", True),
        ("linux", "gnome", False),
        ("win32", "awesome", False),
        ("darwin", "awesome", False),
    ],
)
def test_os_has_awesome_wm(monkeypatch, platform, desktop, expected_result):
    with monkeypatch.context() as m:
        m.setenv("XDG_CURRENT_DESKTOP", desktop)
        m.setattr(info.sys, "platform", platform)
        assert info.has_awesome_wm() == expected_result


@pytest.mark.parametrize(
    ("platform", "xdg_desktop", "gnome_desktop", "gnome_shell", "expected_result"),
    [
        ("linux", "gnome", "gnome", "/usr/bin/gnome-shell", "33.3.0"),
        ("linux", "kde", "", "/usr/bin/gnome-shell", ""),
        ("darwin", "", "", "", ""),
        ("darwin", "", "", "/usr/bin/gnome-shell", ""),
        ("win32", "", "", "", ""),
    ],
)
def test_get_gnome_version(
    platform, xdg_desktop, gnome_desktop, gnome_shell, expected_result, monkeypatch
):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", xdg_desktop)
    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", gnome_desktop)
    monkeypatch.setattr(info.sys, "platform", platform)
    monkeypatch.setattr(
        info.shutil,
        "which",
        lambda x: gnome_shell if x == "gnome-shell" else None,
    )
    monkeypatch.setattr(
        info.subprocess, "check_output", lambda *_, **__: "GNOME Shell 33.3.0"
    )

    assert info.get_gnome_version() == expected_result


# TODO: Parametrize tests?
def test_display_manager_is_wayland_on_windows(monkeypatch):
    monkeypatch.setattr(info.sys, "platform", "win32")
    is_wayland = info.has_wayland_display_manager()
    assert is_wayland is False


def test_display_manager_is_wayland_on_linux_xdg_session_type(monkeypatch):
    monkeypatch.setattr(info.sys, "platform", "linux")

    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    is_wayland = info.has_wayland_display_manager()
    info.has_wayland_display_manager.cache_clear()
    assert is_wayland is True

    monkeypatch.setenv("XDG_SESSION_TYPE", "")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    is_wayland = info.has_wayland_display_manager()
    info.has_wayland_display_manager.cache_clear()
    assert is_wayland is True

    monkeypatch.setenv("XDG_SESSION_TYPE", "gnome-shell")
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    is_wayland = info.has_wayland_display_manager()
    assert is_wayland is False


def test_gnome_version_on_windows(monkeypatch):
    monkeypatch.setattr(info.sys, "platform", "win32")
    version = info.get_gnome_version()
    assert not version


def test_gnome_version_on_linux_from_cmd(monkeypatch):
    monkeypatch.setattr(info.sys, "platform", "linux")
    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "wayland")
    monkeypatch.setattr(info.shutil, "which", lambda _: True)
    info.get_gnome_version.cache_clear()
    version = info.get_gnome_version()
    assert not version

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "gnome")
    monkeypatch.setattr(
        info.subprocess,
        "check_output",
        lambda *args, **kwargs: "GNOME Shell 33.3\n",
    )
    info.get_gnome_version.cache_clear()
    version = info.get_gnome_version()
    assert str(version) == "33.3"


def test_gnome_version_on_linux_without_gnome_shell(monkeypatch):
    monkeypatch.setattr(info.sys, "platform", "linux")
    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "unity")
    info.get_gnome_version.cache_clear()
    version = info.get_gnome_version()
    assert not version

    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "some-id")
    monkeypatch.setattr(info.shutil, "which", lambda _: False)
    info.get_gnome_version.cache_clear()
    version = info.get_gnome_version()
    assert not version


def test_gnome_version_on_linux_unknown_exception(monkeypatch, caplog):
    monkeypatch.setattr(info.sys, "platform", "linux")
    monkeypatch.setattr(info.shutil, "which", lambda _: True)

    def mocked_subprocess(*args, **kwargs):
        raise DivisionByZero()

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "gnome")
    monkeypatch.setattr(info.subprocess, "check_output", mocked_subprocess)
    caplog.set_level(logging.WARNING)

    version = info.get_gnome_version()
    assert not version
    assert "exception when trying to get gnome version" in caplog.text.lower()
