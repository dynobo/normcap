"""Unit tests for main normcap logic."""

# Default
from collections import namedtuple

# Extra
import pytest

# Own
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

    data.line_boxes = [
        LineBox(" one"),
        LineBox("two three "),
        LineBox(" four   "),
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
    assert test_data.lines == "\n".join(["one", "two three", "four"])
