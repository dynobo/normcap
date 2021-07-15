"""Test update checking functionality."""

import pytest

from normcap.update import (
    get_new_version,
    get_newest_github_release,
    get_newest_pypi_release,
)

# Allow pytest fixtures:
# pylint: disable=redefined-outer-name


@pytest.mark.parametrize(
    "func", [get_newest_github_release, get_newest_pypi_release, get_new_version]
)
def test_get_release(func):
    """Retrieve version information from github."""
    release = func()

    assert len(release) >= 5
    assert release[0].isdigit()
    assert release.count(".") == 2
