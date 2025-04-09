import pytest

from normcap.detection.ocr.transformers import email_address


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
    transformed = email_address.transform(ocr_result)

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
    score = email_address.score(ocr_result)

    assert score == score_expected


@pytest.mark.parametrize(
    ("emails", "text", "expected_result_text"),
    [
        (
            ["dynobo@example.com"],
            "Dynobo <dynobo@example.com>",
            " dynobo@example.com ",
        ),
        (
            ["dynobo@example.com", "theo.obonyd@example.com"],
            "Dynobo <dynobo@example.com>; Theo Van Obonyd <theo.obonyd@example.com>",
            " dynobo@example.com Van theo.obonyd@example.com ",
        ),
    ],
)
def test__remove_email_names_from_text(emails, text, expected_result_text):
    text = email_address._remove_email_names_from_text(emails=emails, text=text)
    assert text == expected_result_text
