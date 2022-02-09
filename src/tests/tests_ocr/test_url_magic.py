import pytest  # type: ignore

from normcap.ocr.magics.url_magic import UrlMagic

from .ocr_fixtures import ocr_result  # pylint: disable=unused-import

# pylint: disable=redefined-outer-name,protected-access,unused-argument


@pytest.mark.parametrize(
    "words,transformed_expected,score_expected",
    [
        (
            [
                {"text": "@"},
                {"text": "©"},
                {"text": "https://www.si.org/search?query=pink,blue&page=2"},
            ],
            "https://www.si.org/search?query=pink,blue&page=2",
            77,
        ),
        (
            [{"text": "wWw.qithub,com"}],
            "www.github.com",
            85,
        ),
        (
            [{"text": "https"}, {"text": "://"}, {"text": "dynobo,org"}],
            "https://dynobo.org",
            85,
        ),
        (
            [{"text": "https://"}, {"text": "gooqle.com"}],
            "https://google.com",
            85,
        ),
    ],
)
def test_url_magic_transforms(ocr_result, words, transformed_expected, score_expected):
    """Check some transformations from raw to url."""
    ocr_result.words = words
    url_magic = UrlMagic()
    score = url_magic.score(ocr_result)
    transformed = url_magic.transform(ocr_result)

    assert score > score_expected - 3
    assert score < score_expected + 3
    assert transformed == transformed_expected
