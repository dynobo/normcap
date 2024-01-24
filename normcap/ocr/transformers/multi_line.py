"""Transformer to handle multi line text selection."""

from normcap.ocr.structures import OcrResult


def score(ocr_result: OcrResult) -> float:
    """Calc score based on amount of lines and breaks.

    Arguments:
        ocr_result: Recognized text and meta information.

    Returns:
        Score between 0-100 (100 = more likely)
    """
    if (
        (ocr_result.num_lines > 1)
        and (ocr_result.num_blocks == 1)
        and (ocr_result.num_pars == 1)
    ):
        return 50.0

    return 0


def transform(ocr_result: OcrResult) -> str:
    """Just transform into multiple lines of text.

    Args:
        ocr_result: Recognized text and meta information.

    Returns:
        Lines of text.
    """
    # keep all line breaks as detected:
    return ocr_result.add_linebreaks()
