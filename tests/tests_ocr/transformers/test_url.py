import pytest

from normcap.ocr.transformers import url


@pytest.mark.parametrize(
    ("words", "transformed_expected"),
    [
        (("@", "https://www.si.org/s?q=a,b&pg=2"), "https://www.si.org/s?q=a,b&pg=2"),
        (("wWw.qithub,com",), "https://www.github.com"),
        (("https", "://", "dynobo,org"), "https://dynobo.org"),
        (("https://", "gooqle.com"), "https://google.com"),
    ],
)
def test_url_transformer_transform(ocr_result, words, transformed_expected):
    """Check some transformations from raw to url."""
    ocr_result.words = [{"text": w} for w in words]
    transformed = url.transform(ocr_result)

    assert transformed == transformed_expected


@pytest.mark.parametrize(
    ("words", "score_expected"),
    [
        (("https://www.github.com/search?query=pink,blue&page=2",), 85.0),
        (("www.github,com",), 100.0),
        (("some random words",), 0.0),
    ],
)
def test_url_transformer_score(ocr_result, words, score_expected):
    ocr_result.words = [{"text": w} for w in words]
    score = url.score(ocr_result)

    assert score == score_expected


@pytest.mark.parametrize(
    ("potential_url", "expected_validity"),
    [
        ("www.something.co.uk", True),
        ("www.something.com", True),
        ("http://www.something.com", True),
        ("https://www.something.com", True),
        ("https://www.something.com/", True),
        ("https://www.something.com/www.weired.path", True),
        ("www.something.co.invalid", False),
        ("www.something.invalid", False),
        ("www.something.invalid-com", False),
        ("http://www.something.invalid", False),
        ("https://www.something.invalid", False),
        ("https://www.something.invalid/", False),
        ("https://www.something.invalid/www.weired.path", False),
    ],
)
def test_url_has_valid_tld(potential_url, expected_validity):
    """Check some transformations from raw to url."""
    assert url._has_valid_tld(potential_url) == expected_validity
