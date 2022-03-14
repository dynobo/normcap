import pytest  # type: ignore

from normcap.args import create_argparser
from normcap.gui.settings import Settings

# Specific settings for pytest
# pylint: disable=redefined-outer-name,protected-access,unused-argument


@pytest.fixture(scope="session")
def argparser_defaults():
    argparser = create_argparser()
    return vars(argparser.parse_args([]))


def test_argparser_defaults_are_complete(argparser_defaults):
    args_keys = set(argparser_defaults.keys())
    expected_options = set(
        [
            "color",
            "language",
            "mode",
            "notification",
            "reset",
            "tray",
            "update",
            "verbose",
            "very_verbose",
        ]
    )
    assert args_keys == expected_options


def test_argparser_help_is_complete():
    argparser = create_argparser()
    assert len(argparser.description) > 10
    for action in argparser._actions:
        assert len(action.help) > 10
    assert True


def test_all_argparser_attributes_in_settings(argparser_defaults):
    settings = Settings("normcap", "settings", init_settings={})

    for arg in argparser_defaults:
        if arg in ["verbose", "very_verbose", "reset"]:
            continue
        assert arg in settings.allKeys()

    for key in settings.allKeys():
        assert key in argparser_defaults


def test_argparser_defaults_are_correct(argparser_defaults):
    assert argparser_defaults["reset"] is False
    assert argparser_defaults["verbose"] is False
    assert argparser_defaults["very_verbose"] is False
