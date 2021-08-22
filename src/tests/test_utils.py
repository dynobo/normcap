import os

import pytest  # type: ignore

from normcap import utils


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
