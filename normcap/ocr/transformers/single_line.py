"""Transformer to handle very simple single line text selection."""

from normcap.ocr.structures import OcrResult


def score(ocr_result: OcrResult) -> float:
    """Calc score based on amount of lines.

    Args:
        ocr_result: Recognized text and meta information.

    Returns:
       Score between 0-100 (100 = more likely).
    """
    if len(ocr_result.text) == 0:
        return 1

    return 50 if ocr_result.num_lines == 1 else 0


def transform(ocr_result: OcrResult) -> str:
    """Just transform into single line of text.

    Args:
        ocr_result: Recognized text and meta information.

    Returns:
        Single line of text.
    """
    # Just return concatenated text
    return ocr_result.text.strip()
