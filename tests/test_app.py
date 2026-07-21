import logging
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import normcap

logger = logging.getLogger(__name__)


def test_version():
    with Path("pyproject.toml").open("b", encoding="utf8") as toml_file:
        pyproject_toml = tomllib.load(toml_file)

    pyproject_version = pyproject_toml["project"]["version"]
    normcap_version = normcap.__version__
    assert normcap_version.startswith(pyproject_version)
