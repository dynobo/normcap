"""Unit tests for utils functions."""

# Default
from collections import namedtuple

# Extras
import pytest

# Own
from normcap import utils
from normcap.data_model import NormcapData

# PyLint can't handle fixtures correctly. Ignore.
# pylint: disable=redefined-outer-name


@pytest.fixture(scope="session")
def test_data():
    """Create NormcapData instance for testing."""
    data = NormcapData()
    data.top = 0
    data.bottom = 10
    data.left = 0
    data.right = 20
    LineBox = namedtuple("LineBox", "content")
    data.line_boxes = [LineBox(" one"), LineBox("two three "), LineBox(" four   ")]
    return data


def test_log_dataclass(test_data):
    """Does output contains all data?"""
    expected_strings = [k for k, v in vars(test_data).items()]
    expected_strings += [str(v) for k, v in vars(test_data).items()]
    output = utils.log_dataclass("Test output", test_data, return_string=True)
    assert all([s in output for s in expected_strings])
