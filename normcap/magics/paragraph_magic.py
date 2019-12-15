"""Magic Class to handle paragraph(s) of text."""

# Default
import os

# Own
from normcap.magics.base_magic import BaseMagic
from normcap.common.data_model import NormcapData


class ParagraphMagic(BaseMagic):
    """Detect and extract plain text formatted in paragraphs."""

    name = "paragraph"

    def score(self, request: NormcapData) -> float:
        """Calc score based on layout of amount of paragraphs and blocks.

        Arguments:
            BaseMagic {class} -- Base class for magics
            request {NormcapData} -- NormCap's session data

        Returns:
            float -- score between 0-100 (100 = more likely)
        """
        breaks = request.num_blocks + request.num_pars - 1
        self._final_score = 100 - (100 / (breaks))

        return self._final_score

    def transform(self, request: NormcapData) -> str:
        """Transform wordboxes into nicely formatted paragraphs.

        Arguments:
            request {NormcapData} -- NormCap's session data

        Returns:
            str -- Transformed text
        """
        result = ""
        current_par_num = 1
        current_block_num = 1
        for word in request.words:
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
