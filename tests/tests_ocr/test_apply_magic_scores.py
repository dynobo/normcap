import pytest

from normcap.ocr.magics import Magic


@pytest.mark.parametrize(
    ("words", "scores_expected"),
    [
        (
            (
                {"text": "first", "block_num": 1, "par_num": 1, "line_num": 0},
                {"text": "second", "block_num": 2, "par_num": 1, "line_num": 0},
            ),
            {
                "SingleLineMagic": 50,
                "MultiLineMagic": 0,
                "ParagraphMagic": 50,
                "EmailMagic": 0,
                "UrlMagic": 0,
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
                "SingleLineMagic": 50,
                "MultiLineMagic": 0,
                "ParagraphMagic": 0,
                "EmailMagic": 0,
                "UrlMagic": 78,
            },
        ),
    ],
)
def test_magic_apply_scores(ocr_result, words, scores_expected):
    """Check some transformations from raw to url."""
    ocr_result.words = words
    result = Magic().apply(ocr_result)
    scores = result.magic_scores

    for magic_name in scores:
        assert scores[magic_name] == pytest.approx(
            scores_expected[magic_name], abs=3
        ), magic_name
