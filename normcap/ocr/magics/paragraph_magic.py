"""Magic Class to handle paragraph(s) of text."""

import os

from normcap.ocr.magics.base_magic import BaseMagic
from normcap.ocr.models import OcrResult


class ParagraphMagic(BaseMagic):
    """Detect and extract plain text formatted in paragraphs."""

    def score(self, ocr_result: OcrResult) -> float:
        """Calc score based on layout of amount of paragraphs and blocks.

        Arg:
            ocr_result: Recognized text and meta information.

        Returns:
            Score between 0-100 (100 = more likely).
        """
        breaks = ocr_result.num_blocks + ocr_result.num_pars - 1
        return 100 - (100 / (breaks))

    def transform(self, ocr_result: OcrResult) -> str:
        """Transform word-boxes into nicely formatted paragraphs.

        Args:
            ocr_result: Recognized text and meta information.

        Returns:
            Transformed text.
        """
        # ignore linebreaks within paragraphs:
        return ocr_result.add_linebreaks(block_sep=os.linesep, line_sep=" ")
