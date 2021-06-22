"""Magic Class to handle paragraph(s) of text."""

import os

from normcap.magics.base_magic import BaseMagic
from normcap.models import Capture


class ParagraphMagic(BaseMagic):
    """Detect and extract plain text formatted in paragraphs."""

    def score(self, capture: Capture) -> float:
        """Calc score based on layout of amount of paragraphs and blocks.

        Arguments:
            BaseMagic {class} -- Base class for magics
            capture {Capture} -- NormCap's session data

        Returns:
            float -- score between 0-100 (100 = more likely)
        """
        breaks = capture.num_blocks + capture.num_pars - 1
        self._final_score = 100 - (100 / (breaks))

        return self._final_score

    def transform(self, capture: Capture) -> str:
        """Transform wordboxes into nicely formatted paragraphs.

        Arguments:
            capture {Capture} -- NormCap's session data

        Returns:
            str -- Transformed text
        """
        result = ""
        current_par_num = 1
        current_block_num = 1
        for word in capture.words:
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
