import logging

from normcap.logger import logger


def test_logging_ouput(caplog):
    """Test if logs are received in stdout."""

    test_message = "This is a Test message"
    logger.warning(test_message)
    assert test_message in caplog.text
    assert "warning" in caplog.text.lower()
    assert "normcap:test_logger" in caplog.text


def test_default_level_is_warning():
    """Test for correct default loglevel."""
    assert logger.root.level == logging.WARNING
