import pytest

from normcap.ocr.magics.single_line_magic import SingleLineMagic


@pytest.mark.parametrize(
    "words,transformed_expected",
    [
        ((), ""),
        (("oneword",), "oneword"),
        (("two", "words"), "two words"),
        ((" ", "words", "with", "whitespace", "\n"), "words with whitespace"),
    ],
)
def test_single_line_magic_transform(ocr_result, words, transformed_expected):
    """Check some transformations from raw to url."""
    ocr_result.words = [{"text": w} for w in words]
    magic = SingleLineMagic()
    transformed = magic.transform(ocr_result)

    assert transformed == transformed_expected


@pytest.mark.parametrize(
    "words,score_expected",
    [
        ([], 1),
        ([{"text": "w1", "line_num": 1}], 50),
        ([{"text": "w1", "line_num": 1}, {"text": " ", "line_num": 1}], 50),
        ([{"text": "w1", "line_num": 1}, {"text": "w2", "line_num": 1}], 50),
        ([{"text": "w1", "line_num": 1}, {"text": "w2", "line_num": 2}], 0),
    ],
)
def test_single_line_magic_score(ocr_result, words, score_expected):
    """Check some transformations from raw to url."""
    ocr_result.words = words
    magic = SingleLineMagic()
    score = magic.score(ocr_result)

    assert score == score_expected
