import logging
import sys
from pathlib import Path

import pytest

from normcap.gui import system_info
from normcap.gui.models import DesktopEnvironment, Screen


def test_display_manager_is_wayland(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland")
    system_info.display_manager_is_wayland.cache_clear()
    assert system_info.display_manager_is_wayland()

    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    system_info.display_manager_is_wayland.cache_clear()
    assert system_info.display_manager_is_wayland()


def test_display_manager_is_not_wayland(monkeypatch):
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    system_info.display_manager_is_wayland.cache_clear()
    assert not system_info.display_manager_is_wayland()

    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    monkeypatch.setenv("XDG_SESSION_TYPE", "something")
    system_info.display_manager_is_wayland.cache_clear()
    assert not system_info.display_manager_is_wayland()


def test_desktop_environment():
    assert system_info.desktop_environment() in DesktopEnvironment


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
    system_info.desktop_environment.cache_clear()
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
    environment = system_info.desktop_environment()

    # THEN it should be the one matching the environment variable
    assert environment == expected_environment


def test_is_briefcase_package():
    assert not system_info.is_briefcase_package()

    temp_app_packages = Path(__file__).resolve().parents[3] / "app_packages"
    is_briefcase = False
    try:
        temp_app_packages.mkdir()
        is_briefcase = system_info.is_briefcase_package()
    finally:
        temp_app_packages.rmdir()

    assert is_briefcase


def test_is_flatpak(monkeypatch):
    assert not system_info.is_flatpak()

    with monkeypatch.context() as m:
        m.setenv("FLATPAK_ID", "123")
        assert system_info.is_flatpak()


def test_screens(qtbot):
    screens = system_info.screens()
    assert len(screens) >= 1
    assert all(isinstance(s, Screen) for s in screens)
    assert isinstance(screens[0], Screen)
    assert isinstance(screens[0].width, int)
    assert isinstance(screens[0].height, int)


def test_config_directory_on_windows(monkeypatch, tmp_path):
    with monkeypatch.context() as m:
        m.setattr(sys, "platform", "win32")
        m.setenv("LOCALAPPDATA", str(tmp_path.absolute()))
        system_info.config_directory.cache_clear()
        assert system_info.config_directory() == tmp_path / "normcap"

        m.setenv("LOCALAPPDATA", "")
        m.setenv("APPDATA", str(tmp_path.absolute()))
        system_info.config_directory.cache_clear()
        assert system_info.config_directory() == tmp_path / "normcap"

        m.setenv("LOCALAPPDATA", "")
        m.setenv("APPDATA", "")
        system_info.config_directory.cache_clear()
        with pytest.raises(ValueError, match="Could not determine the appdata"):
            _ = system_info.config_directory()


def test_config_directory_on_linux_macos(monkeypatch, tmp_path):
    with monkeypatch.context() as m:
        m.setattr(sys, "platform", "linux")
        m.setenv("XDG_CONFIG_HOME", str(tmp_path.absolute()))
        config_dir = system_info.config_directory()
    assert config_dir == tmp_path / "normcap"


def test_config_directory_fallback(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(sys, "platform", "unknown")
        m.delenv("XDG_CONFIG_HOME", raising=False)
        config_dir = system_info.config_directory()
    assert config_dir.name == "normcap"
    assert config_dir.parent.name == ".config"


def test_to_dict():
    string = system_info.to_dict()
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
        m.setattr(system_info, "is_briefcase_package", lambda: True)
        m.setattr(system_info.Path, "exists", lambda *args: True)
        m.setattr(system_info.sys, "platform", platform)
        path = system_info.get_tesseract_bin_path(
            is_briefcase_package=system_info.is_briefcase_package()
        )
    assert path.name == binary
    assert path.parent.name == directory


def test_get_tesseract_path_unknown_platform_raises(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(system_info, "is_briefcase_package", lambda: True)
        m.setattr(system_info.Path, "exists", lambda *args: True)
        m.setattr(system_info.sys, "platform", "unknown")
        with pytest.raises(ValueError, match="Platform unknown is not supported"):
            _ = system_info.get_tesseract_bin_path(
                is_briefcase_package=system_info.is_briefcase_package()
            )


def test_get_tesseract_path_missing_binary_raises(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(system_info, "is_briefcase_package", lambda: True)
        with pytest.raises(RuntimeError, match="Could not locate Tesseract binary"):
            _ = system_info.get_tesseract_bin_path(
                is_briefcase_package=system_info.is_briefcase_package()
            )


def test_get_tesseract_path_missing_tesseract_raises(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(system_info.shutil, "which", lambda _: False)
        with pytest.raises(RuntimeError, match="No Tesseract binary found"):
            _ = system_info.get_tesseract_bin_path(
                is_briefcase_package=system_info.is_briefcase_package()
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
    data_file = system_info.config_directory() / "tessdata" / "mocked.traineddata"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.touch(exist_ok=True)

    try:
        with monkeypatch.context() as m:
            m.setattr(system_info, "is_briefcase_package", lambda: is_briefcase)
            m.setattr(system_info, "is_flatpak", lambda: is_flatpak)
            if has_prefix:
                m.setenv("TESSDATA_PREFIX", f"{data_file.resolve().parents[1]}")

            path_briefcase = system_info.get_tessdata_path(
                config_directory=system_info.config_directory(),
                is_briefcase_package=is_briefcase,
                is_flatpak_package=is_flatpak,
            )

            path_end = (
                str(path_briefcase)[-len("tessdata") :] if path_briefcase else None
            )
            assert path_end == expected_path_end

    finally:
        data_file.unlink()


def test_get_tessdata_path_warn_on_win32(monkeypatch, caplog):
    data_file = system_info.config_directory() / "tessdata" / "mocked.traineddata"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.touch(exist_ok=True)

    try:
        with monkeypatch.context() as m:
            m.setattr(system_info, "is_briefcase_package", lambda: False)
            m.setattr(system_info, "is_flatpak", lambda: False)
            m.setenv("TESSDATA_PREFIX", "")

            monkeypatch.setattr(system_info.sys, "platform", "win32")
            with caplog.at_level(logging.WARNING):
                caplog.clear()
                _ = system_info.get_tessdata_path(
                    config_directory=system_info.config_directory(),
                    is_briefcase_package=system_info.is_briefcase_package(),
                    is_flatpak_package=system_info.is_flatpak(),
                )
            assert "TESSDATA_PREFIX" in caplog.records[0].msg

    finally:
        data_file.unlink()
