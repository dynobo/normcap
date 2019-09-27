"""Unit tests for main normcap logic."""

# Default
import logging

# Own
from normcap import normcap

# For Docstrings in pytests, see:
# https://stackoverflow.com/questions/28898919/use-docstrings-to-list-tests-in-py-test


def test_normcap():
    """CaptureHandler should be loaded and not None."""
    assert normcap.CaptureHandler() is not None


def test_init_logging_returns_logger():
    """init_logging() should return a logger."""
    logger = normcap.init_logging(logging.WARNING)
    assert isinstance(logger, logging.Logger)


# def test_parse_cli_args():
#    result = normcap.parse_cli_args()
#    assert isinstance(result, dict)
