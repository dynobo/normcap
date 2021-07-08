"""Test CLI args."""
from dataclasses import fields

import pytest  # type: ignore

from normcap.args import create_argparser
from normcap.models import Config

# Allow pytest fixtures:
# pylint: disable=redefined-outer-name
# Allow usint privates:
# pylint: disable=protected-access


@pytest.fixture(scope="session")
def argparser_defaults():
    """Create argparser and provide its default values."""
    argparser = create_argparser()
    return vars(argparser.parse_args([]))


def test_argparser_defaults_complete(argparser_defaults):
    """Check if all default options are available."""
    args_keys = set(argparser_defaults.keys())
    expected_options = set(
        [
            "color",
            "languages",
            "mode",
            "no_notifications",
            "tray",
            "updates",
            "verbose",
            "very_verbose",
        ]
    )
    assert args_keys == expected_options


def test_argparser_help_complete():
    """Check if commandline arguments have help texts."""
    argparser = create_argparser()
    assert len(argparser.description) > 10
    for action in argparser._actions:
        assert len(action.help) > 10
    assert True


def test_argparser_attributes_in_config_class(argparser_defaults):
    """Check if every args has an attribute in Config class."""
    attributes = [f.name for f in fields(Config)]
    for arg in argparser_defaults:
        if arg in ["verbose", "very_verbose", "no_notifications"]:
            continue
        assert arg in attributes


def test_argparser_default_verbose(argparser_defaults):
    """Check verbose (for loglevel)."""
    assert argparser_defaults["verbose"] is False


def test_argparser_default_no_notifications(argparser_defaults):
    """Check no notifications."""
    assert argparser_defaults["no_notifications"] is False


def test_argparser_default_lang(argparser_defaults):
    """Check OCR language."""
    assert argparser_defaults["languages"] == "eng"


def test_argparser_default_color(argparser_defaults):
    """Check accent color."""
    assert argparser_defaults["color"] == "#FF2E88"
