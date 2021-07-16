import os

import pytest  # type: ignore

from normcap import models, utils


def test_get_display_manager():
    """Check if display manager enum is returned."""
    dm = utils.get_display_manager()
    assert dm in models.DisplayManager


def test_get_desktop_environment():
    """Check if display manager enum is returned."""
    de = utils.get_desktop_environment()
    assert de in models.DesktopEnvironment


def test_get_platform():
    """Check if platform enum is returned."""
    platform = utils.get_platform()
    assert platform in models.Platform


def test_environment_context_manager():
    """Test if context manger sets env var temporarily."""
    assert os.environ.get("TEST_ENV") is None

    # Normal run
    with utils.temporary_environ(TEST_ENV="123"):
        assert os.environ.get("TEST_ENV") == "123"

    assert os.environ.get("TEST_ENV") is None

    # Interrupted by exception run
    with pytest.raises(ZeroDivisionError):
        with utils.temporary_environ(TEST_ENV="123"):
            assert os.environ.get("TEST_ENV") == "123"
            _ = 1 / 0

    assert os.environ.get("TEST_ENV") is None
