import logging
import sys
from pathlib import Path

import pytest
import toml

import normcap
from normcap import app, utils

logger = logging.getLogger(__name__)


def test_version():
    with Path("pyproject.toml").open(encoding="utf8") as toml_file:
        pyproject_toml = toml.load(toml_file)

    pyproject_version = pyproject_toml["project"]["version"]
    normcap_version = normcap.__version__
    assert normcap_version.startswith(pyproject_version)


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
        args = app._get_args()

    assert args.parse_text is False
    assert args.language == ["eng", "deu"]
    assert args.tray is True


def test_get_args_version(monkeypatch, capsys):
    with monkeypatch.context() as m:
        m.setattr(sys, "argv", [sys.argv[0], "--version"])
        with pytest.raises(SystemExit) as exc:
            _ = app._get_args()

    output = capsys.readouterr()
    assert normcap.__version__ in output.out
    assert not output.err
    assert exc.value.code == 0


@pytest.mark.parametrize(
    ("arg_value", "expected_level"),
    [("info", logging.INFO), ("debug", logging.DEBUG)],
)
def test_prepare_logging(monkeypatch, arg_value, expected_level, caplog):
    with monkeypatch.context() as m:
        m.setattr(sys, "argv", [sys.argv[0], "--verbosity", arg_value])
        args = app._get_args()

    app._prepare_logging(getattr(args, "verbosity", "ERROR"))
    logger = logging.getLogger("normcap")

    assert logger.level == expected_level
    assert sys.excepthook == utils.hook_exceptions


def test_prepare_env():
    app._prepare_envs()
