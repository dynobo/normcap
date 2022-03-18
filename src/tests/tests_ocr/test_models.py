from .ocr_fixtures import ocr_result  # pylint: disable=unused-import

# Specific settings for pytest
# pylint: disable=redefined-outer-name,protected-access,unused-argument


def test_ocr_result(ocr_result):
    """Check if calulated properties are working correctely."""
    assert isinstance(ocr_result.text, str)
    assert ocr_result.text.count("\n") == 0
    assert ocr_result.text.count(" ") >= 2
    assert ocr_result.text.startswith("one")

    assert isinstance(ocr_result.lines, str)
    lines = ocr_result.lines.splitlines()
    assert len(lines) == 2
    assert lines[0] == "one two"

    assert ocr_result.num_blocks == 2
    assert ocr_result.num_pars == 3
    assert ocr_result.num_lines == 2

    assert ocr_result.mean_conf == 30
    ocr_result.words = []
    assert ocr_result.mean_conf == 0

    assert ocr_result.best_scored_magic is None
    ocr_result.magic_scores = dict(email=1.0, url=0.7, paragraph=0)
    assert ocr_result.best_scored_magic == "email"
