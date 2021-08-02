import pytest  # type: ignore

from normcap.args import create_argparser
from normcap.gui.settings import init_settings

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


def test_argparser_help_complete():
    """Check if commandline arguments have help texts."""
    argparser = create_argparser()
    assert len(argparser.description) > 10
    for action in argparser._actions:
        assert len(action.help) > 10
    assert True


def test_argparser_attributes_in_settings(argparser_defaults):
    """Check if every setting has an cli args an vice versa."""
    settings = init_settings({})

    for arg in argparser_defaults:
        if arg in ["verbose", "very_verbose", "reset"]:
            continue
        assert arg in settings.allKeys()

    for key in settings.allKeys():
        assert key in argparser_defaults


def test_argparser_check_defaults(argparser_defaults):
    """Check verbose (for loglevel)."""
    assert argparser_defaults["reset"] is False
    assert argparser_defaults["verbose"] is False
    assert argparser_defaults["very_verbose"] is False
