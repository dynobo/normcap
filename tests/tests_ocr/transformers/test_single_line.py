import pytest

from normcap.ocr.transformers import single_line


@pytest.mark.parametrize(
    ("words", "transformed_expected"),
    [
        ((), ""),
        (("oneword",), "oneword"),
        (("two", "words"), "two words"),
        ((" ", "words", "with", "whitespace", "\n"), "words with whitespace"),
    ],
)
def test_single_line_transformer_transform(ocr_result, words, transformed_expected):
    """Check some transformations from raw to url."""
    ocr_result.words = [{"text": w} for w in words]
    transformed = single_line.transform(ocr_result)

    assert transformed == transformed_expected


@pytest.mark.parametrize(
    ("words", "score_expected"),
    [
        ([], 1),
        ([{"text": "w1", "line_num": 1}], 50),
        ([{"text": "w1", "line_num": 1}, {"text": " ", "line_num": 1}], 50),
        ([{"text": "w1", "line_num": 1}, {"text": "w2", "line_num": 1}], 50),
        ([{"text": "w1", "line_num": 1}, {"text": "w2", "line_num": 2}], 0),
    ],
)
def test_single_line_transformer_score(ocr_result, words, score_expected):
    """Check some transformations from raw to url."""
    ocr_result.words = words
    score = single_line.score(ocr_result)

    assert score == score_expected
