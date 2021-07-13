"""Test image enhancing methods."""
import os
import tempfile
from pathlib import Path

from normcap.models import Config, ConfigBase

# pylint: disable=no-member # dataclass magics are not recognized


def test_persisted_config_repr():
    """Check if repr includes all fields correct."""
    temp_config = Path(tempfile.gettempdir()) / "config.temp"
    try:
        config = Config(file_path=temp_config)
    finally:
        os.unlink(temp_config)

    string = str(config)
    for field in config.__dataclass_fields__:  # type: ignore
        assert field in string


def test_persisted_config_is_same_as_config():
    """Check if the datafield of normal and persisted config are the same."""
    temp_config = Path(tempfile.gettempdir()) / "config.temp"
    try:
        persisted_config = Config(file_path=temp_config)
    finally:
        os.unlink(temp_config)

    config = ConfigBase()
    persisted_config_fields = set(persisted_config.__dataclass_fields__)  # type: ignore
    config_fields = set(config.__dataclass_fields__)  # type: ignore # pylint: disable=no-member

    assert persisted_config_fields == config_fields


def test_persistance():
    """Check if the datafield of normal and persisted config are the same."""
    # Create config file
    temp_config = Path(tempfile.gettempdir()) / "config.temp"

    try:
        # Init with defaults
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
        # Delete config file
        os.unlink(temp_config)

    assert initial_value != loaded_value
    assert new_value == loaded_value
