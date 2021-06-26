"""Test image enhancing methods."""
import os
import tempfile
from pathlib import Path

from normcap.models import Config, ConfigBase

# pylint: disable=no-member # dataclass magics are not recognized


def test_persisted_config_repr():
    """Check if repr includes all fields correct."""
    with tempfile.NamedTemporaryFile() as cf:
        config = Config(file_path=Path(cf.name))

    string = str(config)
    for field in config.__dataclass_fields__:  # type: ignore
        assert field in string


def test_persisted_config_is_same_as_config():
    """Check if the datafield of normal and persisted config are the same."""
    with tempfile.NamedTemporaryFile() as cf:
        persisted_config = Config(file_path=Path(cf.name))
    config = ConfigBase()

    persisted_config_fields = set(persisted_config.__dataclass_fields__)  # type: ignore
    config_fields = set(config.__dataclass_fields__)  # type: ignore # pylint: disable=no-member

    assert persisted_config_fields == config_fields


def test_persistance():
    """Check if the datafield of normal and persisted config are the same."""
    # Create config file
    temp_path = Path.cwd() / "test_config.tmp"

    try:
        # Init with defaults
        config = Config(file_path=temp_path)
        initial_value = config.languages

        # Set new value
        new_value = tuple(list(initial_value) + ["xyz"])
        config.languages = new_value

        # Reload config
        del config
        config = Config(file_path=temp_path)
        loaded_value = config.languages
    finally:
        # Delete config file
        os.unlink(temp_path)

    assert initial_value != loaded_value
    assert new_value == loaded_value
