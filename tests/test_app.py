import logging
from pathlib import Path

import toml

import normcap

logger = logging.getLogger(__name__)


def test_version():
    with Path("pyproject.toml").open(encoding="utf8") as toml_file:
        pyproject_toml = toml.load(toml_file)

    pyproject_version = pyproject_toml["project"]["version"]
    normcap_version = normcap.__version__
    assert normcap_version.startswith(pyproject_version)
