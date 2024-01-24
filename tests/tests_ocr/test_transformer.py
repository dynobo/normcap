import pytest

from normcap.ocr import transformer
from normcap.ocr.structures import Transformer


@pytest.mark.parametrize(
    ("words", "scores_expected"),
    [
        (
            (
                {"text": "first", "block_num": 1, "par_num": 1, "line_num": 0},
                {"text": "second", "block_num": 2, "par_num": 1, "line_num": 0},
            ),
            {
                Transformer.SINGLE_LINE: 50,
                Transformer.MULTI_LINE: 0,
                Transformer.PARAGRAPH: 50,
                Transformer.MAIL: 0,
                Transformer.URL: 0,
            },
        ),
        (
            (
                {"text": "@", "block_num": 1, "par_num": 1, "line_num": 0},
                {"text": "©", "block_num": 1, "par_num": 1, "line_num": 0},
                {
                    "text": "https://www.si.org/search?query=pink,blue&page=2",
                    "block_num": 1,
                    "par_num": 1,
                    "line_num": 0,
                },
            ),
            {
                Transformer.SINGLE_LINE: 50,
                Transformer.MULTI_LINE: 0,
                Transformer.PARAGRAPH: 0,
                Transformer.MAIL: 0,
                Transformer.URL: 78,
            },
        ),
    ],
)
def test_transformer_apply_scores(ocr_result, words, scores_expected):
    """Check some transformations from raw to url."""
    ocr_result.words = words
    result = transformer.apply(ocr_result)
    scores = result.transformer_scores

    for transformer_name in scores:
        assert scores[transformer_name] == pytest.approx(
            scores_expected[transformer_name], abs=3
        ), transformer_name
