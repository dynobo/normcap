import sys

import pytest

from normcap import __version__, argparser
from normcap.gui.settings import Settings


def test_get_args_version(monkeypatch, capsys):
    with monkeypatch.context() as m:
        m.setattr(sys, "argv", [sys.argv[0], "--version"])
        with pytest.raises(SystemExit) as exc:
            _ = argparser.get_args()

    output = capsys.readouterr()
    assert __version__ in output.out
    assert not output.err
    assert exc.value.code == 0


def test_argparser_defaults_are_complete():
    # GIVEN the argparser parses empty cli args
    parser = argparser._create_argparser()

    # WHEN it parses an empty list of args
    parsed_args = parser.parse_args([])

    # THEN an expected set of options should be present with default values
    expected_options = {
        "background_mode",
        "cli_mode",
        "clipboard_handler",
        "color",
        "dbus_activation",
        "detect_codes",
        "detect_text",
        "language",
        "log_file",
        "notification_handler",
        "notification",
        "parse_text",
        "reset",
        "screenshot_handler",
        "show_introduction",
        "tray",
        "update",
        "verbosity",
        "version",
    }
    args_keys = set(vars(parsed_args).keys())
    assert args_keys == expected_options


def test_argparser_help_is_complete():
    # WHEN instantiating the argparser
    argparser_ = argparser._create_argparser()

    # THEN it should contain a description
    #    and all actions should have a help text
    assert argparser_.description
    assert len(argparser_.description) > 10

    for action in argparser_._actions:
        assert action.help
        assert len(action.help) > 10


def test_argparser_parses_all_types(monkeypatch):
    # GIVEN an argparser
    argparser_ = argparser._create_argparser()

    # WHEN parsing a list of args with string representing various types
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "python",
            "--notification",
            "True",
            "--tray",
            "0",
            "--verbosity",
            "info",
            "--language",
            "uvw",
            "xyz",
        ],
    )
    args = argparser_.parse_args()

    # THEN the various types should be parsed into the correct types
    assert args.notification is True
    assert args.tray is False
    assert args.verbosity == "info"
    assert args.language == ["uvw", "xyz"]


def test_argparser_attributes_in_settings():
    argparser_defaults = vars(argparser._create_argparser().parse_args([]))
    settings = Settings(organization="normcap_TEST")
    args_without_setting = {
        "background_mode",
        "cli_mode",
        "clipboard_handler",
        "dbus_activation",
        "log_file",
        "notification_handler",
        "reset",
        "screenshot_handler",
        "verbosity",
        "version",
    }
    for arg in argparser_defaults:
        if arg in args_without_setting:
            continue
        assert arg.replace("_", "-") in settings.allKeys()


def test_settings_in_argparser_attributes():
    argparser_defaults = vars(argparser._create_argparser().parse_args([]))
    settings = Settings(organization="normcap_TEST")
    settings_without_arg = {
        "current-version",
        "last-update-check",
        "has-screenshot-permission",
    }
    for key in settings.allKeys():
        if key in settings_without_arg:
            continue
        assert key.replace("-", "_") in argparser_defaults


def test_argparser_defaults_are_correct():
    argparser_defaults = vars(argparser._create_argparser().parse_args([]))
    assert argparser_defaults.pop("reset") is False
    assert argparser_defaults.pop("version") is False
    assert argparser_defaults.pop("cli_mode") is False
    assert argparser_defaults.pop("background_mode") is False
    assert argparser_defaults.pop("dbus_activation") is False
    assert argparser_defaults.pop("verbosity") == "warning"
    for value in argparser_defaults.values():
        assert value is None


def test_get_args(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(
            sys,
            "argv",
            [
                sys.argv[0],
                "--language",
                "eng",
                "deu",
                "--parse-text=False",
                "--tray=True",
            ],
        )
        args = argparser.get_args()

    assert args.parse_text is False
    assert args.language == ["eng", "deu"]
    assert args.tray is True
