import os
from pathlib import Path

import importlib_metadata
import pytest

from normcap import models, system_info


def test_display_manager():
    """Check if display manager enum is returned."""
    assert system_info.display_manager() in models.DisplayManager


def test_desktop_environment():
    """Check if display manager enum is returned."""
    assert system_info.desktop_environment() in models.DesktopEnvironment


def test_primary_screen_idx(monkeypatch):
    """Check if calulated properties are working correctely."""

    def _screens(has_primary: bool):
        return {
            0: models.ScreenInfo(
                is_primary=False,
                index=0,
                device_pixel_ratio=1,
                geometry=models.Rect(),
            ),
            1: models.ScreenInfo(
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
    """Check if package detection works."""
    assert not system_info.is_briefcase_package()

    monkeypatch.setattr(
        importlib_metadata, "metadata", lambda _: {"Briefcase-Version": "9.9.9"}
    )
    assert system_info.is_briefcase_package()


def test_screens(qtbot):  # pylint: disable=unused-argument
    """Check screen info types and content."""
    screens = system_info.screens()
    assert len(screens) >= 1
    assert all(isinstance(i, int) for i in screens)
    assert set(screens.keys()) == set(range(len(screens)))
    assert isinstance(screens[0], models.ScreenInfo)
    assert isinstance(screens[0].width, int)
    assert isinstance(screens[0].height, int)


def test_get_tessdata_path(monkeypatch):
    """Check tessdata path in / outside package."""
    # pylint: disable=protected-access

    data_file = system_info.config_directory() / "tessdata" / "mocked.traineddata"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.touch(exist_ok=True)

    try:
        monkeypatch.setattr(system_info, "is_briefcase_package", lambda: True)
        path_briefcase = system_info._get_tessdata_path()

        monkeypatch.setattr(system_info, "is_briefcase_package", lambda: False)
        monkeypatch.setenv("TESSDATA_PREFIX", str(data_file.parent.parent.resolve()))
        path_env_var = system_info._get_tessdata_path()

        monkeypatch.setattr(system_info, "is_briefcase_package", lambda: False)
        monkeypatch.setenv("TESSDATA_PREFIX", "")
        path_non = system_info._get_tessdata_path()
    finally:
        data_file.unlink()

    assert path_briefcase.endswith("tessdata" + os.sep)
    assert path_env_var.endswith("tessdata" + os.sep)
    assert path_non == ""

    # mock directory but _no_ language data:
    monkeypatch.setattr(system_info, "config_directory", lambda: Path("/tmp"))
    monkeypatch.setattr(system_info, "is_briefcase_package", lambda: True)
    with pytest.raises(RuntimeError):
        _ = system_info._get_tessdata_path()


def test_tesseract():
    """Check tesseract system info."""
    system_info.tesseract.cache_clear()
    infos = system_info.tesseract()

    assert isinstance(infos, models.TesseractInfo)

    version = infos.version.split(".")
    assert version[0].isdigit()
    assert len(version) == 3

    assert infos.path == "" or infos.path[-1] in ["\\", "/"]
    assert Path(infos.path).exists()

    assert isinstance(infos.languages, list)
    assert len(infos.languages) >= 1


def test_tesseract_exceptions(monkeypatch):
    """Check tesseract system info."""

    def simulate_raise():
        raise RuntimeError()

    monkeypatch.setattr(
        system_info.pytesseract, "get_tesseract_version", simulate_raise
    )

    with pytest.raises(RuntimeError):
        system_info.tesseract.cache_clear()
        _ = system_info.tesseract()


def test_to_string():
    """Check if str represeentation contains expected infos."""
    system_info.tesseract.cache_clear()
    string = system_info.to_string()
    expected = []
    for item in expected:
        assert item in string
