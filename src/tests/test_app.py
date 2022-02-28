import logging

import toml
from packaging.version import Version

import normcap

logger = logging.getLogger(__name__)

# Specific settings for pytest
# pylint: disable=redefined-outer-name,protected-access,unused-argument


def test_version():
    with open("pyproject.toml", encoding="utf8") as toml_file:
        pyproject_toml = toml.load(toml_file)

    briefcase_version = Version(pyproject_toml["tool"]["briefcase"]["version"])
    poetry_version = Version(pyproject_toml["tool"]["poetry"]["version"])
    normcap_version = Version(normcap.__version__)
    assert briefcase_version >= poetry_version == normcap_version
