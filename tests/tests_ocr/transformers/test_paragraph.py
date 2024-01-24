import os

import pytest

from normcap.ocr.transformers import paragraph


@pytest.mark.parametrize(
    ("words", "transformed_expected"),
    [
        (
            (
                {"text": "first", "block_num": 1, "par_num": 1},
                {"text": "second", "block_num": 2, "par_num": 1},
            ),
            f"first{os.linesep}second",
        ),
        (
            (
                {"text": "first", "block_num": 1, "par_num": 1},
                {"text": "second", "block_num": 1, "par_num": 2},
            ),
            f"first{os.linesep}second",
        ),
        (
            (
                {"text": "first", "block_num": 1, "par_num": 1},
                {"text": "second", "block_num": 2, "par_num": 1},
                {"text": "third ", "block_num": 2, "par_num": 2},
            ),
            f"first{os.linesep}second{os.linesep}third",
        ),
    ],
)
def test_url_paragraph_transforms(ocr_result, words, transformed_expected):
    """Check some transformations from raw to url."""
    ocr_result.words = words
    paragraph.score(ocr_result)
    transformed = paragraph.transform(ocr_result)

    assert transformed == transformed_expected
