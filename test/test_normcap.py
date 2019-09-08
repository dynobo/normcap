"""Unit tests for main normcap logic."""

from normcap import normcap

# For Docstrings in pytests, see:
# https://stackoverflow.com/questions/28898919/use-docstrings-to-list-tests-in-py-test


def test_normcap():
    """CaptureHandler should be loaded and not None."""
    assert normcap.CaptureHandler() is not None
