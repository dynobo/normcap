"""Unit tests for main normcap logic."""

# Default
import logging
import os
import tempfile

# Extra
import pytest
from PIL import Image

# Own
from normcap import normcap
from normcap.common.data_model import NormcapData
from normcap.common import utils
from normcap.handlers.abstract_handler import AbstractHandler
from .images.test_images import TEST_IMAGES

# PyLint can't handle fixtures correctly. Ignore.
# pylint: disable=redefined-outer-name


def test_version():
    """Are we testing right version?"""
    assert normcap.__version__ == "0.1.11"


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

    result = normcap.client_code(test_handler_1, 1)
    assert result == 4


# TESTING CLi arguments
# ==========================


@pytest.fixture(scope="session")
def argparser_defaults():
    """Create argparser and provide its default values."""
    argparser = normcap.create_argparser()
    return vars(argparser.parse_args([]))


def test_argparser_defaults_complete(argparser_defaults):
    """Check if all default options are available."""
    args_keys = set(argparser_defaults.keys())
    expected_options = set(
        ["verbose", "mode", "lang", "no_notifications", "color", "path"]
    )
    assert args_keys == expected_options


def test_argparser_default_verbose(argparser_defaults):
    """Check verbose (for loglevel)."""
    assert argparser_defaults["verbose"] is False


def test_argparser_default_mode(argparser_defaults):
    """Check default capture mode."""
    assert argparser_defaults["mode"] == "parse"


def test_argparser_default_no_notifications(argparser_defaults):
    """Check no notifications."""
    assert argparser_defaults["no_notifications"] is False


def test_argparser_default_lang(argparser_defaults):
    """Check OCR language."""
    assert argparser_defaults["lang"] == "eng"


def test_argparser_default_color(argparser_defaults):
    """Check accent color."""
    assert argparser_defaults["color"] == "#BF616A"


def test_argparser_default_path(argparser_defaults):
    """Check path to store images."""
    assert argparser_defaults["path"] is None


# TESTING init_logging()
# ==========================


@pytest.mark.parametrize("to_file", [True, False])
def test_init_logging_returns_logger(to_file):
    """init_logging() should return a logger."""
    logger = normcap.init_logging(logging.WARNING, to_file=to_file)
    assert isinstance(logger, logging.Logger)


# TESTING main():
# ==========================


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


all_confs = []


@pytest.mark.parametrize("test_params", TEST_IMAGES)
def test_normcap_main(pytestconfig, test_params):
    """Load various images and apply OCR pipeline."""
    test_data = data_test_image(test_params)

    print(f"Test ID: {test_params['test_id']}")

    result = normcap.main(test_data)

    similarity = utils.get_jaccard_sim(
        result.transformed.split(), test_params["expected_result"].split()
    )

    assert similarity >= test_params["expected_similarity"]
    assert result.best_magic == test_params["expected_magic"]
    if test_params.get("expected_doublelinebreaks", False):
        result_paragraphs = result.transformed.count(os.linesep * 2)
        assert result_paragraphs == test_params["expected_doublelinebreaks"]

    # Additional infos to be reported
    all_confs.append((result.mean_conf, similarity, test_params["explanation"]))
    pytestconfig.all_confs = all_confs
