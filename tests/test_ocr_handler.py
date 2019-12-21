"""Unit tests for ocr handler."""

# Own
from normcap.handlers.ocr_handler import OcrHandler
from .test_data_model import test_data  # noqa  # flake 8 can't handle fixtures


def test_ocr_handler_language_selection(test_data):  # noqa
    """Test if not available languages are filtered out."""
    ocr = OcrHandler()
    result = ocr.handle(test_data)
    assert result.cli_args["lang"] == "eng+deu"
