import pytest

from normcap.ocr.magics.url_magic import UrlMagic


@pytest.mark.parametrize(
    "words,transformed_expected",
    [
        (("@", "https://www.si.org/s?q=a,b&pg=2"), "https://www.si.org/s?q=a,b&pg=2"),
        (("wWw.qithub,com",), "https://www.github.com"),
        (("https", "://", "dynobo,org"), "https://dynobo.org"),
        (("https://", "gooqle.com"), "https://google.com"),
    ],
)
def test_url_magic_transform(ocr_result, words, transformed_expected):
    """Check some transformations from raw to url."""
    ocr_result.words = [{"text": w} for w in words]
    magic = UrlMagic()
    transformed = magic.transform(ocr_result)

    assert transformed == transformed_expected


@pytest.mark.parametrize(
    "words,score_expected",
    (
        (("https://www.github.com/search?query=pink,blue&page=2",), 85.0),
        (("www.github,com",), 100.0),
        (("some random words",), 0.0),
    ),
)
def test_url_magic_score(ocr_result, words, score_expected):
    ocr_result.words = [{"text": w} for w in words]
    magic = UrlMagic()
    score = magic.score(ocr_result)

    assert score == score_expected
