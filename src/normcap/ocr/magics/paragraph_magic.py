"""Magic Class to handle paragraph(s) of text."""

import os

from normcap.ocr.magics.base_magic import BaseMagic
from normcap.ocr.models import OcrResult


class ParagraphMagic(BaseMagic):
    """Detect and extract plain text formatted in paragraphs."""

    def score(self, ocr_result: OcrResult) -> float:
        """Calc score based on layout of amount of paragraphs and blocks.

        Arguments:
            BaseMagic {class} -- Base class for magics
            capture {Capture} -- NormCap's session data

        Returns:
            float -- score between 0-100 (100 = more likely)
        """
        breaks = ocr_result.num_blocks + ocr_result.num_pars - 1
        return 100 - (100 / (breaks))

    def transform(self, ocr_result: OcrResult) -> str:
        """Transform wordboxes into nicely formatted paragraphs.

        Arguments:
            capture {Capture} -- NormCap's session data

        Returns:
            str -- Transformed text
        """
        result = ""
        current_par_num = 1
        current_block_num = 1
        for word in ocr_result.words:
            breaks = 0
            if word["par_num"] != current_par_num:
                current_par_num = word["par_num"]
                breaks = 2
            if word["block_num"] != current_block_num:
                current_block_num = word["block_num"]
                breaks = 2

            if breaks > 0:
                # New line
                result += os.linesep * breaks + word["text"]
            else:
                # No new line
                result += " " + word["text"]

        return result.strip()
