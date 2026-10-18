import logging
import tomllib
from pathlib import Path

import normcap

logger = logging.getLogger(__name__)


def test_version():
    with Path("pyproject.toml").open("rb") as toml_file:
        pyproject_toml = tomllib.load(toml_file)

    pyproject_version = pyproject_toml["project"]["version"]
    normcap_version = normcap.__version__
    assert normcap_version.startswith(pyproject_version)
