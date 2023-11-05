import pytest

from normcap.ocr.magics import url_utils


@pytest.mark.parametrize(
    ("url", "expected_validity"),
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
def test_url_magic_transform(url, expected_validity):
    """Check some transformations from raw to url."""
    assert url_utils.has_valid_tld(url) == expected_validity
