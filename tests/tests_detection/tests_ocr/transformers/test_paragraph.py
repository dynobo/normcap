import os

import pytest

from normcap.detection.ocr.transformers.paragraph import ParagraphTransformer


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
    transformer = ParagraphTransformer()
    transformer.score(ocr_result)
    transformed = transformer.transform(ocr_result)

    assert len(transformed) == 1

    assert transformed[0] == transformed_expected
