import pytest  # type: ignore

from normcap.magics.url_magic import UrlMagic

# pylint: disable=unused-import
from .fixtures import capture

# Allow pytest fixtures:
# pylint: disable=redefined-outer-name


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
def test_url_magic_transforms(capture, words, transformed_expected, score_expected):
    """Check some transformations from raw to url."""
    capture.words = words
    url_magic = UrlMagic()
    score = url_magic.score(capture)
    transformed = url_magic.transform(capture)

    assert score > score_expected - 3
    assert score < score_expected + 3
    assert transformed == transformed_expected
