import toml

import normcap

# PyLint can't handle fixtures correctly. Ignore.
# pylint: disable=redefined-outer-name


def test_version():
    """Check version string consistency"""

    with open("pyproject.toml") as toml_file:
        pyproject_toml = toml.load(toml_file)

    briefcase_version = pyproject_toml["tool"]["briefcase"]["version"]
    poetry_version = pyproject_toml["tool"]["poetry"]["version"]
    assert briefcase_version == poetry_version == normcap.__version__
