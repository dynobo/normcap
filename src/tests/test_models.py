import tempfile
from pathlib import Path

import pytest  # type: ignore
from PySide2 import QtGui

from normcap.models import (
    Capture,
    Config,
    ConfigBase,
    Rect,
    SystemInfo,
    _format_section,
)

# pylint: disable=unused-import
from .fixtures import capture, system_info

# Allow pytest fixtures:
# pylint: disable=redefined-outer-name
# Allow usint privates:
# pylint: disable=protected-access


def test_format_section():
    """Check if formatting works."""
    text = "This Is a Dummy Text\n\n"
    result = _format_section(text, "DummySection")

    assert result[0] == "\n"
    assert result.count("DummySection") == 2
    assert result[-1] != "\n"
    assert result.count("\n\n") == 0


def test_rect():
    """Check if calulated properties are working correctely."""
    rect = Rect(left=10, top=20, right=110, bottom=220)
    assert rect.width == 100
    assert rect.height == 200
    assert rect.points == (10, 20, 110, 220)
    assert rect.geometry == (10, 20, 100, 200)


def test_system_info(system_info: SystemInfo):
    """Check if calulated properties are working correctely."""
    assert system_info.primary_screen_idx == 1

    system_info.screens[1].is_primary = False
    with pytest.raises(ValueError):
        _ = system_info.primary_screen_idx

    string = str(system_info)
    for field in system_info.__dict__:
        assert field in string

    assert isinstance(system_info.screens[0].width, int)
    assert isinstance(system_info.screens[0].height, int)


def test_config_repr():
    """Check if config values are actually persisted."""
    temp_config = Path(tempfile.gettempdir()) / "config.tmp"
    try:
        config = Config(file_path=temp_config)
        config_string = str(config)
        config_fields = config.__dataclass_fields__
    finally:
        temp_config.unlink()

    for field in config_fields:
        assert field in config_string


def test_config_change_attribute():
    """Check if config values are actually persisted."""
    temp_config = Path(tempfile.gettempdir()) / "config.tmp"
    try:
        config = Config(file_path=temp_config)

        # Setting to same value won't trigger save
        setattr(config, "color", "#00ff00")

        # Setting to different value will trigger save
        setattr(config, "color", "#ffffff")
    finally:
        temp_config.unlink()


def test_config_persists():
    """Check if config values are actually persisted."""
    temp_config = Path(tempfile.gettempdir()) / "config.tmp"
    try:
        config = Config(file_path=temp_config)
        initial_value = config.languages

        # Set new value
        new_value = tuple(list(initial_value) + ["xyz"])
        config.languages = new_value

        # Reload config
        del config
        config = Config(file_path=temp_config)
        loaded_value = config.languages
    finally:
        temp_config.unlink()

    assert initial_value != loaded_value
    assert new_value == loaded_value


def test_config_persistance_invalid_file():
    """Check if we get error if no valid file is used"""
    # Get directory instead file
    temp_config = Path(tempfile.gettempdir())

    with pytest.raises(ValueError):
        _ = Config(file_path=temp_config)


def test_persisted_config_repr():
    """Check if repr includes all fields correct."""
    temp_config = Path(tempfile.gettempdir()) / "config.temp"
    try:
        config = Config(file_path=temp_config)
    finally:
        temp_config.unlink()

    string = str(config)
    # pylint: disable=no-member
    # type: ignore
    for field in config.__dataclass_fields__:
        assert field in string


def test_persisted_config_is_same_as_config():
    """Check if the datafield of normal and persisted config are the same."""
    temp_config = Path(tempfile.gettempdir()) / "config.temp"
    try:
        persisted_config = Config(file_path=temp_config)
    finally:
        temp_config.unlink()

    config = ConfigBase()
    # pylint: disable=no-member
    # type: ignore
    persisted_config_fields = set(persisted_config.__dataclass_fields__)
    config_fields = set(config.__dataclass_fields__)

    assert persisted_config_fields == config_fields


def test_persisted_config_reads_empty_file():
    """Defaults should be loaded if config file is empty."""
    temp_config = Path(tempfile.gettempdir()) / "config.temp"
    temp_config.touch()
    try:
        persisted_config = Config(file_path=temp_config)
    finally:
        temp_config.unlink()

    config = ConfigBase()
    assert persisted_config.color == config.color
    assert persisted_config.languages == config.languages


def test_capture(capture: Capture):
    """Check if calulated properties are working correctely."""
    capture.image = QtGui.QImage(200, 300, QtGui.QImage.Format.Format_RGB32)
    capture.image.fill(QtGui.QColor("#ff0000"))

    string = str(capture)
    for field in capture.__dict__:
        assert field in string

    assert capture.image_area == 60_000
    capture.image = QtGui.QImage()
    assert capture.image_area == 0

    assert isinstance(capture.text, str)
    assert capture.text.count("\n") == 0
    assert capture.text.count(" ") >= 2
    assert capture.text.startswith("one")

    assert isinstance(capture.lines, str)
    lines = capture.lines.splitlines()
    assert len(lines) == 2
    assert lines[0] == "one two"

    assert capture.num_blocks == 2
    assert capture.num_pars == 3
    assert capture.num_lines == 2

    assert capture.mean_conf == 30
    capture.words = []
    assert capture.mean_conf == 0

    capture.image = None  # type: ignore
    assert capture.image_area == 0
