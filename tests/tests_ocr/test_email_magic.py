import pytest

from normcap.ocr.magics.email_magic import EmailMagic


@pytest.mark.parametrize(
    "words,transformed_expected",
    [
        (("dy@no.bo",), "dy@no.bo"),
        ((" dy@no.bo ",), "dy@no.bo"),
        (("dy@no.bo.uk",), "dy@no.bo.uk"),
        (("mail:", "dy@no.bo"), "dy@no.bo"),
        (("dy@no.bo", "no@bo.dy"), "dy@no.bo, no@bo.dy"),
        (("dyn@dyno",), ""),
    ],
)
def test_email_magic_transform(ocr_result, words, transformed_expected):
    """Check some transformations from raw to url."""
    ocr_result.words = [{"text": w} for w in words]
    magic = EmailMagic()
    transformed = magic.transform(ocr_result)

    assert transformed == transformed_expected


@pytest.mark.parametrize(
    "words,score_expected",
    [
        (("dy@no.bo",), 100),
        ((" dy@no.bo ",), 80),
        (("dy@no.bo.uk",), 100),
        (("to", "dy@no.bo"), 80),
        (("dy@no.bo", "no@bo.dy"), 100),
        (("dyn@dyno",), 0),
    ],
)
def test_email_magic_score(ocr_result, words, score_expected):
    ocr_result.words = [{"text": w} for w in words]
    magic = EmailMagic()
    score = magic.score(ocr_result)

    assert score == score_expected
