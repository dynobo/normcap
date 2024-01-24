import pytest

from normcap.ocr.transformers import email


@pytest.mark.parametrize(
    ("words", "transformed_expected"),
    [
        (("dy@no.bo",), "dy@no.bo"),
        ((" dy@no.bo ",), "dy@no.bo"),
        (("dy@no.bo.uk",), "dy@no.bo.uk"),
        (("mail:", "dy@no.bo"), "dy@no.bo"),
        (("dy@no.bo", "no@bo.dy"), "dy@no.bo, no@bo.dy"),
        (("dyn@dyno",), ""),
    ],
)
def test_email_transformer_transform(ocr_result, words, transformed_expected):
    """Check some transformations from raw to url."""
    ocr_result.words = [{"text": w} for w in words]
    transformed = email.transform(ocr_result)

    assert transformed == transformed_expected


@pytest.mark.parametrize(
    ("words", "score_expected"),
    [
        (("dy@no.bo",), 100),
        ((" dy@no.bo ",), 100),
        (("dy@no.bo.uk",), 100),
        (("to", "dy@no.bo"), 80),
        (("dy@no.bo", "no@bo.dy"), 100),
        (("dyn@dyno",), 0),
    ],
)
def test_email_transformer_score(ocr_result, words, score_expected):
    ocr_result.words = [{"text": w} for w in words]
    score = email.score(ocr_result)

    assert score == score_expected
