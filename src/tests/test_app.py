import logging
import sys

import normcap
import pytest
import toml
from normcap import app
from normcap.version import Version

logger = logging.getLogger(__name__)


def test_version():
    with open("pyproject.toml", encoding="utf8") as toml_file:
        pyproject_toml = toml.load(toml_file)

    briefcase_version = Version(pyproject_toml["tool"]["briefcase"]["version"])
    poetry_version = Version(pyproject_toml["tool"]["poetry"]["version"])
    normcap_version = Version(normcap.__version__)
    assert briefcase_version >= poetry_version == normcap_version


def test_get_args(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(
            sys,
            "argv",
            [sys.argv[0], "--language", "eng", "deu", "--mode=raw", "--tray=True"],
        )
        args = app._get_args()

    assert args.mode == "raw"
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
    "level,result",
    (
        ("info", {"level": logging.INFO, "has_hook": True}),
        ("debug", {"level": logging.DEBUG, "has_hook": False}),
    ),
)
def test_prepare_logging(monkeypatch, level, result, caplog):
    with monkeypatch.context() as m:
        m.setattr(sys, "argv", [sys.argv[0], "--verbosity", level])
        args = app._get_args()

    app._prepare_logging(args)
    logger = logging.getLogger("normcap")

    assert logger.level == result["level"]
    assert (sys.excepthook == normcap.utils.hook_exceptions) is result["has_hook"]


def test_prepare_env():
    app._prepare_envs()
