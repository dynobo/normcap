import sys
from pathlib import Path

import pytest
from normcap.gui import models, system_info


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

    monkeypatch.setenv("WAYLAND_DISPLAY", "something")
    monkeypatch.setenv("XDG_SESSION_TYPE", "something")
    system_info.display_manager_is_wayland.cache_clear()
    assert not system_info.display_manager_is_wayland()


def test_desktop_environment():
    system_info.desktop_environment.cache_clear()
    assert system_info.desktop_environment() in models.DesktopEnvironment


def test_desktop_environment_gnome(monkeypatch):
    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "1")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "")
    system_info.desktop_environment.cache_clear()
    assert system_info.desktop_environment() == models.DesktopEnvironment.GNOME

    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "gnome")
    system_info.desktop_environment.cache_clear()
    assert system_info.desktop_environment() == models.DesktopEnvironment.GNOME


def test_desktop_environment_kde(monkeypatch):
    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "")

    monkeypatch.setenv("KDE_FULL_SESSION", "1")
    monkeypatch.setenv("DESKTOP_SESSION", "")
    system_info.desktop_environment.cache_clear()
    assert system_info.desktop_environment() == models.DesktopEnvironment.KDE

    monkeypatch.setenv("KDE_FULL_SESSION", "")
    monkeypatch.setenv("DESKTOP_SESSION", "kde-plasma")
    system_info.desktop_environment.cache_clear()
    assert system_info.desktop_environment() == models.DesktopEnvironment.KDE


def test_desktop_environment_sway(monkeypatch):
    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "")
    monkeypatch.setenv("KDE_FULL_SESSION", "")
    monkeypatch.setenv("DESKTOP_SESSION", "")

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "sway")
    system_info.desktop_environment.cache_clear()
    assert system_info.desktop_environment() == models.DesktopEnvironment.SWAY


def test_desktop_environment_other(monkeypatch):
    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "")
    monkeypatch.setenv("KDE_FULL_SESSION", "")
    monkeypatch.setenv("DESKTOP_SESSION", "")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "")

    system_info.desktop_environment.cache_clear()
    assert system_info.desktop_environment() == models.DesktopEnvironment.OTHER


def test_is_briefcase_package():
    assert not system_info.is_briefcase_package()

    temp_app_packages = Path(__file__).parent.parent.parent.parent / "app_packages"
    is_briefcase = False
    try:
        temp_app_packages.mkdir()
        is_briefcase = system_info.is_briefcase_package()
    finally:
        temp_app_packages.rmdir()

    assert is_briefcase


def test_is_flatpak_package(monkeypatch):
    assert not system_info.is_flatpak_package()

    with monkeypatch.context() as m:
        m.setenv("FLATPAK_ID", "123")
        assert system_info.is_flatpak_package()


def test_screens():
    screens = system_info.screens()
    assert len(screens) >= 1
    assert all(isinstance(s, models.Screen) for s in screens)
    assert isinstance(screens[0], models.Screen)
    assert isinstance(screens[0].width, int)
    assert isinstance(screens[0].height, int)


def test_get_tessdata_path(monkeypatch, tmp_path):
    data_file = system_info.config_directory() / "tessdata" / "mocked.traineddata"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.touch(exist_ok=True)

    try:
        with monkeypatch.context() as m:
            m.setattr(system_info, "is_briefcase_package", lambda: True)
            m.setattr(system_info, "is_flatpak_package", lambda: False)
            path_briefcase = system_info.get_tessdata_path()

            m.setattr(system_info, "is_briefcase_package", lambda: False)
            m.setattr(system_info, "is_flatpak_package", lambda: True)
            path_flatpak = system_info.get_tessdata_path()

            m.setattr(system_info, "is_briefcase_package", lambda: False)
            m.setattr(system_info, "is_flatpak_package", lambda: False)
            m.setenv("TESSDATA_PREFIX", f"{data_file.parent.parent.resolve()}")
            path_env_var = system_info.get_tessdata_path()
            m.setenv("TESSDATA_PREFIX", "")
            path_non = system_info.get_tessdata_path()
    finally:
        data_file.unlink()

    assert str(path_briefcase).endswith("tessdata")
    assert str(path_flatpak).endswith("tessdata")
    assert str(path_env_var).endswith("tessdata")
    assert path_non is None


def test_config_directory_retrieved_on_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path.absolute()))
    system_info.config_directory.cache_clear()
    assert system_info.config_directory() == tmp_path / "normcap"

    monkeypatch.setenv("LOCALAPPDATA", "")
    monkeypatch.setenv("APPDATA", str(tmp_path.absolute()))
    system_info.config_directory.cache_clear()
    assert system_info.config_directory() == tmp_path / "normcap"

    monkeypatch.setenv("LOCALAPPDATA", "")
    monkeypatch.setenv("APPDATA", "")
    system_info.config_directory.cache_clear()
    with pytest.raises(ValueError) as e:
        _ = system_info.config_directory()
    assert "could not determine the appdata" in str(e.value).lower()


def test_config_directory_retrieved_on_linux_macos(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path.absolute()))
    assert system_info.config_directory() == tmp_path / "normcap"


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
        "gnome_version",
        "screens",
    ]
    for item in expected:
        assert item in string
