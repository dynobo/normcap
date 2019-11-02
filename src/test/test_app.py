"""Unit tests for main normcap logic."""

# Default
import logging
import json
import os
import tempfile

# Extra
import pytest
from PIL import Image
import Levenshtein

# Own
from normcap import app
from normcap.common.data_model import NormcapData
from normcap.common import utils
from normcap.handlers.abstract_handler import AbstractHandler


# PyLint can't handle fixtures correctly. Ignore.
# pylint: disable=redefined-outer-name


def test_version():
    """Are we testing right version?"""
    assert app.VERSION == "0.1a1"


# TESTING client_code()
# ==========================


def test_client_code_handler():
    """CaptureHandler should be loaded and not None."""

    class AddOneHandler(AbstractHandler):
        """Dummy handler for testing."""

        def handle(self, request: int) -> int:
            """Add 1 to input and return."""
            request += 1
            if self._next_handler:
                return super().handle(request)
            else:
                return request

    test_handler_1 = AddOneHandler()
    test_handler_2 = AddOneHandler()
    test_handler_3 = AddOneHandler()

    test_handler_1.set_next(test_handler_2).set_next(test_handler_3)

    result = app.client_code(test_handler_1, 1)
    assert result == 4


# TESTING init_logging()
# ==========================


@pytest.mark.parametrize("to_file", [True, False])
def test_init_logging_returns_logger(to_file):
    """init_logging() should return a logger."""
    logger = app.init_logging(logging.WARNING, to_file=to_file)
    assert isinstance(logger, logging.Logger)


# TESTING main():
# ==========================


def get_test_params():
    """Load test parameters from json."""
    test_img_folder = os.path.dirname(os.path.abspath(__file__)) + "/images/"
    json_file = test_img_folder + "test_images.json"

    with open(json_file) as data_file:
        data = json.load(data_file)
        test_params_list = data["images"]

    return test_params_list


def data_test_image(test_params):
    """Create NormcapData instance for testing."""
    data = NormcapData()
    data.test_mode = True
    data.cli_args = test_params["cli_args"]
    data.top = test_params["position"]["top"]
    data.bottom = test_params["position"]["bottom"]
    data.left = test_params["position"]["left"]
    data.right = test_params["position"]["right"]
    data.mode = test_params["cli_args"]["mode"]

    # Prep images
    test_img_folder = os.path.dirname(os.path.abspath(__file__)) + "/images/"
    img = Image.open(test_img_folder + test_params["filename"])
    data.shots = [{"monitor": 0, "image": img}]

    # Set tempfolder for storing
    data.cli_args["path"] = tempfile.gettempdir()

    return data


@pytest.mark.parametrize("test_params", get_test_params())
def test_normcap_main(test_params):
    """Load various images and apply OCR pipeline."""
    test_data = data_test_image(test_params)
    result = app.main(test_data)

    print(utils.log_dataclass("Test output", result, return_string=True))

    rel_lev = Levenshtein.ratio(result.transformed, test_params["expected_result"])

    assert (rel_lev >= test_params["expected_accuracy"]) and (
        result.best_magic == test_params["expected_magic"]
    )
