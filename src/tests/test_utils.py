import os
from importlib import metadata

import pytest

from normcap import utils
from normcap.gui.settings import Settings


def test_argparser_defaults_are_complete(argparser_defaults):
    args_keys = set(argparser_defaults.keys())
    expected_options = {
        "color",
        "language",
        "mode",
        "notification",
        "reset",
        "tray",
        "update",
        "verbosity",
    }

    assert args_keys == expected_options


def test_argparser_help_is_complete():
    argparser = utils.create_argparser()
    assert len(argparser.description) > 10
    for action in argparser._actions:  # pylint: disable=protected-access
        assert len(action.help) > 10
    assert True


def test_all_argparser_attributes_in_settings(argparser_defaults):
    settings = Settings("normcap", "settings", init_settings={})

    for arg in argparser_defaults:
        if arg in ["verbosity", "reset"]:
            continue
        assert arg in settings.allKeys()

    for key in settings.allKeys():
        assert key in argparser_defaults


def test_argparser_defaults_are_correct(argparser_defaults):
    assert argparser_defaults.pop("reset") is False
    assert argparser_defaults.pop("verbosity") == "warning"
    for value in argparser_defaults.values():
        assert value is None


@pytest.mark.parametrize("os_str", ("linux", "win32", "darwin"))
def test_set_environ_for_briefcase_not_packaged(monkeypatch, os_str):
    monkeypatch.setattr(utils.metadata, "metadata", lambda _: [])
    monkeypatch.setattr(utils.sys, "platform", os_str)

    tesseract_cmd = os.environ.get("TESSERACT_CMD", None)
    tesseract_version = os.environ.get("TESSERACT_VERSION", None)

    utils.set_environ_for_briefcase()  # pylint: disable=protected-access

    assert tesseract_cmd == os.environ.get("TESSERACT_CMD", None)
    assert tesseract_version == os.environ.get("TESSERACT_VERSION", None)


@pytest.mark.parametrize("os_str", ("darwin", "linux", "win32"))
def test_set_environ_for_briefcase_is_packaged(monkeypatch, os_str):

    monkeypatch.setattr(metadata, "metadata", lambda _: ["Briefcase-Version"])
    monkeypatch.setattr(utils.sys, "platform", os_str)
    monkeypatch.setattr(utils.sys.modules["__main__"], "__package__", "normcap")

    monkeypatch.setenv("TESSERACT_CMD", "")
    monkeypatch.setenv("TESSERACT_VERSION", "")

    utils.set_environ_for_briefcase()  # pylint: disable=protected-access

    if os_str == "win32":
        assert os.environ.get("TESSERACT_CMD").endswith("tesseract.exe")
        assert os.environ.get("TESSERACT_VERSION")
    else:
        assert os.environ.get("TESSERACT_CMD").endswith("tesseract")
