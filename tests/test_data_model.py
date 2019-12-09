"""Unit tests for main normcap logic."""

# Default
import os

# Extra
import pytest

# Own
from normcap.common.data_model import NormcapData

# PyLint can't handle fixtures correctly. Ignore.
# pylint: disable=redefined-outer-name


@pytest.fixture(scope="session")
def test_data():
    """Create NormcapData instance for testing."""
    data = NormcapData()
    data.test_mode = True
    data.top = 0
    data.bottom = 10
    data.left = 0
    data.right = 20
    data.words = [
        {"line_num": 1, "text": "one"},
        {"line_num": 2, "text": "two"},
        {"line_num": 2, "text": "three"},
        {"line_num": 3, "text": "four"},
    ]  # Space to check trimming
    return data


def test_data_model_selected_area(test_data):
    """Check if image area is calculated correctely."""
    assert test_data.selected_area == 200


def test_data_model_text(test_data):
    """Check if lines are concatinated correctely."""
    assert test_data.text == "one two three four"


def test_data_model_lines(test_data):
    """Check if lines are concatinated correctely with linebreaks."""
    assert test_data.lines == os.linesep.join(["one", "two three", "four"])
