# Extra
import pytest

# Own
import run

# TESTING create_argparser()
# ==========================


@pytest.fixture(scope="session")
def argparser_defaults():
    """Create argparser and provide its default values."""
    argparser = run.create_argparser()
    return vars(argparser.parse_args([]))


def test_argparser_defaults_complete(argparser_defaults):
    """Check if all default options are available."""
    args_keys = set(argparser_defaults.keys())
    expected_options = set(["verbose", "mode", "lang", "color", "path"])
    assert args_keys == expected_options


def test_argparser_default_verbose(argparser_defaults):
    """Check verbose (for loglevel)."""
    assert argparser_defaults["verbose"] is False


def test_argparser_default_mode(argparser_defaults):
    """Check default capture mode."""
    assert argparser_defaults["mode"] == "trigger"


def test_argparser_default_lang(argparser_defaults):
    """Check OCR language."""
    assert argparser_defaults["lang"] == "eng"


def test_argparser_default_color(argparser_defaults):
    """Check accent color."""
    assert argparser_defaults["color"] == "#FF0000"


def test_argparser_default_path(argparser_defaults):
    """Check path to store images."""
    assert argparser_defaults["path"] is None
