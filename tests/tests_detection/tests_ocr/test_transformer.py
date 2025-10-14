import pytest

from normcap.detection.ocr import transformer
from normcap.detection.ocr.models import Transformer


@pytest.mark.parametrize(
    ("words", "scores_expected"),
    [
        (
            (
                {"text": "first", "block_num": 1, "par_num": 1, "line_num": 0},
                {"text": "second", "block_num": 2, "par_num": 1, "line_num": 0},
            ),
            {
                Transformer.SINGLE_LINE: 50,
                Transformer.MULTI_LINE: 0,
                Transformer.PARAGRAPH: 50,
                Transformer.MAIL: 0,
                Transformer.URL: 0,
            },
        ),
        (
            (
                {"text": "@", "block_num": 1, "par_num": 1, "line_num": 0},
                {"text": "©", "block_num": 1, "par_num": 1, "line_num": 0},
                {
                    "text": "https://www.si.org/search?query=pink,blue&page=2",
                    "block_num": 1,
                    "par_num": 1,
                    "line_num": 0,
                },
            ),
            {
                Transformer.SINGLE_LINE: 50,
                Transformer.MULTI_LINE: 0,
                Transformer.PARAGRAPH: 0,
                Transformer.MAIL: 0,
                Transformer.URL: 78,
            },
        ),
    ],
)
def test_transformer_apply_scores(ocr_result, words, scores_expected):
    """Check some transformations from raw to url."""
    ocr_result.words = words
    result = transformer.apply(ocr_result)
    scores = result.transformer_scores

    for transformer_name in scores:
        assert scores[transformer_name] == pytest.approx(
            scores_expected[transformer_name], abs=3
        ), transformer_name


@pytest.mark.parametrize(
    ("lang", "expected"),
    [
        ("chi_sim", True),
        ("chi_tra", True),
        ("chi_sim_vert", True),
        ("jpn", True),
        ("kor", True),
        ("eng", False),
        ("deu", False),
        ("chi_sim+eng", True),  # Mixed with Chinese
        ("eng+deu", False),  # No CJK
    ],
)
def test_should_strip_whitespaces(lang, expected):
    """Test detection of CJK languages that benefit from whitespace stripping."""
    result = transformer._should_strip_whitespaces(lang)
    assert result == expected


@pytest.mark.parametrize(
    ("input_text", "expected"),
    [
        # Soft line breaks (no punctuation) should be removed
        ("这是第一行\n这是第二行", "这是第一行这是第二行"),
        ("多行文本\n继续\n还继续", "多行文本继续还继续"),
        
        # Hard line breaks (after punctuation) should be kept
        ("这是句子。\n这是新句子。", "这是句子。\n这是新句子。"),
        ("句子一。\n句子二！\n句子三？", "句子一。\n句子二！\n句子三？"),
        
        # Spaces between CJK characters should be removed
        ("这是 中文 文本", "这是中文文本"),
        ("中 文 字 符", "中文字符"),
        
        # Spaces around English words should be kept
        ("这是 English word 混排", "这是 English word 混排"),
        ("PDF 文档识别", "PDF 文档识别"),
        
        # Paragraph breaks (double newlines) should become single newline
        ("第一段。\n\n第二段。", "第一段。\n第二段。"),
        ("段落一\n\n段落二\n\n段落三", "段落一\n段落二\n段落三"),
        
        # Mixed scenarios
        ("中文English中文", "中文English中文"),
        ("行尾\n继续行", "行尾继续行"),
        ("句子结束。\n\n新段落开始", "句子结束。\n新段落开始"),
    ],
)
def test_strip_chinese_whitespaces(input_text, expected):
    """Test smart whitespace stripping for CJK text mixed with Latin text."""
    result = transformer._strip_chinese_whitespaces(input_text)
    assert result == expected
