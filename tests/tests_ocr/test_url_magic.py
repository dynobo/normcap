import pytest

from normcap.ocr.magics.url_magic import UrlMagic


@pytest.mark.parametrize(
    "words,transformed_expected",
    [
        (
            ("@", "©", "https://www.si.org/search?query=pink,blue&page=2"),
            "https://www.si.org/search?query=pink,blue&page=2",
        ),
        (
            ("wWw.qithub,com",),
            "https://www.github.com",
        ),
        (
            ("https", "://", "dynobo,org"),
            "https://dynobo.org",
        ),
        (
            ("https://", "gooqle.com"),
            "https://google.com",
        ),
    ],
)
def test_url_magic_transforms(ocr_result, words, transformed_expected):
    """Check some transformations from raw to url."""
    ocr_result.words = [{"text": w} for w in words]
    magic = UrlMagic()
    magic.score(ocr_result)
    transformed = magic.transform(ocr_result)

    assert transformed == transformed_expected
