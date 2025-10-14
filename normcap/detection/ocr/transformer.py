"""Pick and apply individual transformers to OCR results."""

import logging
import re

from normcap.detection.ocr import transformers
from normcap.detection.ocr.models import OcrResult, Transformer, TransformerProtocol

logger = logging.getLogger(__name__)

_transformers: dict[Transformer, TransformerProtocol] = {
    Transformer.SINGLE_LINE: transformers.single_line,
    Transformer.MULTI_LINE: transformers.multi_line,
    Transformer.PARAGRAPH: transformers.paragraph,
    Transformer.MAIL: transformers.email_address,
    Transformer.URL: transformers.url,
}


def apply(ocr_result: OcrResult, strip_whitespaces: bool = False) -> OcrResult:
    """Load transformers, calculate score, execute transformer with highest score.

    Args:
        ocr_result: Recognized text and meta information.

    Returns:
        Enriched NormCap's session data.
    """
    # Get score per transformer
    ocr_result.transformer_scores = _calc_scores(ocr_result)

    # Transform with best transformer
    if best_transformer_name := ocr_result.best_scored_transformer:
        best_transformer = _transformers[best_transformer_name]
        ocr_result.parsed = best_transformer.transform(ocr_result)
    else:
        # No transformer matched, use raw OCR text
        ocr_result.parsed = ocr_result.add_linebreaks()

    ocr_result.parsed = _post_process(ocr_result, strip_whitespaces)
    return ocr_result


def _clean(text: str) -> str:
    """Replace commonly used some utf-8 chars by simplified ones."""
    # Double quotations marks and primes
    text = re.sub(r"[„”“‟″‶ʺ]", '"', text)
    # Singe quotation marks
    text = re.sub(r"[‚‘’‛]", "'", text)  # noqa: RUF001  # ambiguous string
    return text  # unnecessary return for clarity


def _post_process(ocr_result: OcrResult, strip_whitespaces: bool = False) -> str:
    """Apply postprocessing to transformed output."""
    text = ocr_result.parsed
    text = _clean(text)
    # Smart whitespace stripping for CJK text
    logger.debug(
        "Whitespace stripping: enabled=%s, should_strip=%s, lang=%s",
        strip_whitespaces,
        _should_strip_whitespaces(ocr_result.tess_args.lang) if strip_whitespaces else "N/A",
        ocr_result.tess_args.lang,
    )
    if strip_whitespaces and _should_strip_whitespaces(ocr_result.tess_args.lang):
        logger.debug("Before smart stripping: %s", repr(text[:100]))
        text = _strip_chinese_whitespaces(text)
        logger.debug("After smart stripping: %s", repr(text[:100]))
    return text


def _should_strip_whitespaces(lang: str) -> bool:
    """Check if language contains CJK characters that benefit from smart stripping.
    
    Now checks for Chinese, Japanese, or Korean languages.
    """
    selected_languages = lang.split("+")
    cjk_langs = {"chi_", "jpn", "kor"}
    return any(
        any(sel_lang.startswith(cjk_prefix) for cjk_prefix in cjk_langs)
        for sel_lang in selected_languages
    )


def _strip_chinese_whitespaces(text: str) -> str:
    """Smart whitespace stripping for CJK text mixed with Latin text.
    
    Rules:
    - Remove spaces between CJK characters only (keep spaces for English words)
    - Remove soft line breaks (after non-punctuation characters)
    - Keep hard line breaks (after end punctuation like 。！？；：)
    - Keep paragraph breaks (double newlines -> single newline)
    
    This smart algorithm works well for mixed CJK-Latin text.
    """
    # Define CJK character range (Chinese, Japanese, Korean)
    cjk_pattern = r'[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f\uff00-\uffef]'
    # End punctuation that indicates sentence end
    end_punct_pattern = r'[。！？；：]'
    
    # Step 1: Handle paragraph breaks (double newlines)
    text = re.sub(r'\n\n+', '<<<PARAGRAPH>>>', text)
    
    # Step 2: Handle line breaks intelligently
    lines = text.split('\n')
    result = []
    for i, line in enumerate(lines):
        if i < len(lines) - 1:  # Not the last line
            # Check if line ends with end punctuation
            if re.search(end_punct_pattern + r'$', line.rstrip()):
                # Hard break after punctuation - keep newline
                result.append(line.rstrip() + '\n')
            else:
                # Soft break - remove newline
                result.append(line.rstrip())
        else:
            result.append(line.rstrip())
    text = ''.join(result)
    
    # Step 3: Remove spaces adjacent to CJK characters (but preserve ASCII word spacing)
    # Remove: CJK + space + non-letter
    text = re.sub(f'({cjk_pattern})[ \t]+(?![a-zA-Z])', r'\1', text)
    # Remove: non-letter + space + CJK
    text = re.sub(f'(?<![a-zA-Z])[ \t]+({cjk_pattern})', r'\1', text)
    
    # Step 4: Restore paragraph breaks as single newline
    text = text.replace('<<<PARAGRAPH>>>', '\n')
    
    return text
def _calc_scores(ocr_result: OcrResult) -> dict[Transformer, float]:
    """Calculate score for every loaded transformer.

    Arguments:
        ocr_result: Recognized text and meta information.

    Returns:
        Scores in format {<transformer>: <score>}.
    """
    scores = {
        name: transformer.score(ocr_result)
        for name, transformer in _transformers.items()
    }
    logger.debug("Transformer scores:\n%s", scores)
    return scores
