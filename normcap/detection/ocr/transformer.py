"""Pick and apply individual transformers to OCR results."""

import logging
import re

from normcap.detection.ocr import transformers
from normcap.detection.ocr.models import OcrResult, Transformer, TransformerProtocol

logger = logging.getLogger(__name__)

_transformers: dict[Transformer, TransformerProtocol] = {
    Transformer.SINGLE_LINE: transformers.single_line.SingleLineTransformer(),
    Transformer.MULTI_LINE: transformers.multi_line.MultiLineTransformer(),
    Transformer.PARAGRAPH: transformers.paragraph.ParagraphTransformer(),
    Transformer.MAIL: transformers.email_address.EmailTransformer(),
    Transformer.URL: transformers.url.UrlTransformer(),
}


def apply(ocr_result: OcrResult) -> OcrResult:
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

    ocr_result.parsed = _post_process(ocr_result)
    return ocr_result


def _clean(text: str) -> str:
    """Replace commonly used some utf-8 chars by simplified ones."""
    # Double quotations marks and primes
    text = re.sub(r"[„”“‟″‶ʺ]", '"', text)
    # Singe quotation marks
    text = re.sub(r"[‚‘’‛]", "'", text)  # noqa: RUF001  # ambiguous string
    return text  # unnecessary return for clarity


def _post_process(ocr_result: OcrResult) -> list[str]:
    """Apply postprocessing to transformed output."""
    texts = ocr_result.parsed
    texts = [_clean(t) for t in texts]
    # ONHOLD: Check tesseract issue if whitespace workaround still necessary:
    # https://github.com/tesseract-ocr/tesseract/issues/2702
    if ocr_result.tess_args.is_language_without_spaces():
        texts = [t.replace(" ", "") for t in texts]
    return texts


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
