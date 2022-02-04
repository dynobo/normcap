import subprocess
import sys
from distutils.version import LooseVersion
from importlib import metadata
from pathlib import Path

import pytest

from normcap import models, system_info

# Specific settings for pytest
# pylint: disable=redefined-outer-name,protected-access,unused-argument


def test_gnome_shell_version_on_gnome(monkeypatch):
    version = LooseVersion("40.1")
    monkeypatch.setattr(
        subprocess,
        "check_output",
        lambda cmd, shell: f"Gnome Shell {version}\n ".encode("utf-8"),
    )
    system_info.gnome_shell_version.cache_clear()
    assert system_info.gnome_shell_version() == version


def test_gnome_shell_version_on_linux_without_gnome(monkeypatch):
    def raise_process_error(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "gnome-shell --version")

    monkeypatch.setattr(subprocess, "check_output", raise_process_error)
    system_info.gnome_shell_version.cache_clear()
    assert system_info.gnome_shell_version() is None


def test_gnome_shell_version_on_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    system_info.gnome_shell_version.cache_clear()
    assert system_info.gnome_shell_version() is None


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


def test_primary_screen_idx(monkeypatch):
    def _screens(has_primary: bool):
        return {
            0: models.Screen(
                is_primary=False,
                index=0,
                device_pixel_ratio=1,
                geometry=models.Rect(),
            ),
            1: models.Screen(
                is_primary=has_primary,
                index=1,
                device_pixel_ratio=1.5,
                geometry=models.Rect(),
            ),
        }

    monkeypatch.setattr(system_info, "screens", lambda: _screens(True))
    assert system_info.primary_screen_idx() == 1

    monkeypatch.setattr(system_info, "screens", lambda: _screens(False))
    with pytest.raises(ValueError):
        _ = system_info.primary_screen_idx()


def test_is_briefcase_package(monkeypatch):
    assert not system_info.is_briefcase_package()

    monkeypatch.setattr(metadata, "metadata", lambda _: {"Briefcase-Version": "9.9.9"})
    monkeypatch.setattr(sys.modules["__main__"], "__package__", "normcap")
    assert system_info.is_briefcase_package()


def test_screens(qtbot):
    screens = system_info.screens()
    assert len(screens) >= 1
    assert all(isinstance(i, int) for i in screens)
    assert set(screens.keys()) == set(range(len(screens)))
    assert isinstance(screens[0], models.Screen)
    assert isinstance(screens[0].width, int)
    assert isinstance(screens[0].height, int)


def test_get_tessdata_path(monkeypatch, tmp_path):
    data_file = system_info.config_directory() / "tessdata" / "mocked.traineddata"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.touch(exist_ok=True)

    try:
        monkeypatch.setattr(system_info, "is_briefcase_package", lambda: True)
        path_briefcase = system_info.get_tessdata_path()

        monkeypatch.setattr(system_info, "is_briefcase_package", lambda: False)
        monkeypatch.setenv("TESSDATA_PREFIX", str(data_file.parent.parent.resolve()))
        path_env_var = system_info.get_tessdata_path()

        monkeypatch.setattr(system_info, "is_briefcase_package", lambda: False)
        monkeypatch.setenv("TESSDATA_PREFIX", "")
        path_non = system_info.get_tessdata_path()
    finally:
        data_file.unlink()

    assert path_briefcase.endswith("tessdata")
    assert path_env_var.endswith("tessdata")
    assert path_non == ""

    # mock config dir not existing:
    monkeypatch.setattr(system_info, "is_briefcase_package", lambda: True)
    monkeypatch.setattr(system_info, "config_directory", lambda: tmp_path / "nan")
    with pytest.raises(RuntimeError) as e:
        _ = system_info.get_tessdata_path()
    assert "tessdata directory does not exist" in str(e.value).lower()

    # mock language dir not containing traineddata:
    (tmp_path / "tessdata").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(system_info, "config_directory", lambda: tmp_path)
    with pytest.raises(RuntimeError) as e:
        _ = system_info.get_tessdata_path()
    assert "could not find language data files" in str(e.value).lower()

    # mock directory but _no_ language data:
    monkeypatch.setattr(system_info, "config_directory", lambda: Path("/tmp"))
    monkeypatch.setattr(system_info, "is_briefcase_package", lambda: True)
    with pytest.raises(RuntimeError):
        _ = system_info.get_tessdata_path()


def test_config_directory_retrieved_on_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path.absolute()))
    assert system_info.config_directory() == tmp_path / "normcap"

    monkeypatch.setenv("LOCALAPPDATA", "")
    monkeypatch.setenv("APPDATA", str(tmp_path.absolute()))
    assert system_info.config_directory() == tmp_path / "normcap"

    monkeypatch.setenv("LOCALAPPDATA", "")
    monkeypatch.setenv("APPDATA", "")
    with pytest.raises(ValueError) as e:
        _ = system_info.config_directory()
    assert "could not determine the appdata" in str(e.value).lower()


def test_config_directory_retrieved_on_linux_macos(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path.absolute()))
    assert system_info.config_directory() == tmp_path / "normcap"


def test_to_string():
    string = system_info.to_string()
    expected = [
        "cli_args",
        "is_briefcase_package",
        "platform",
        "pyside6_version",
        "qt_version",
        "qt_library_path",
        "config_directory",
        "normcap_version",
        "tessdata_path",
        "desktop_environment",
        "display_manager_is_wayland",
        "gnome_shell_version",
        "screens",
    ]
    for item in expected:
        assert item in string
