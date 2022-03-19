"""Magic Class to handle very simple single line text selection."""

from normcap.ocr.magics.base_magic import BaseMagic
from normcap.ocr.models import OcrResult


class SingleLineMagic(BaseMagic):
    """Format a single line of text."""

    def score(self, ocr_result: OcrResult) -> float:
        """Calc score based on amount of lines.

        Arguments:
            BaseMagic {class} -- Base class for magics
            capture {Capture} -- NormCap's session data

        Returns:
            float -- score between 0-100 (100 = more likely)
        """
        if len(ocr_result.text) == 0:
            return 1

        if ocr_result.num_lines == 1:
            return 50

        return 0

    def transform(self, ocr_result: OcrResult) -> str:
        """Just transform into single line of text.

        Arguments:
            capture {Capture} -- NormCap's session data

        Returns:
            str -- Single line of text
        """
        # Just return concatenated text
        return ocr_result.text.strip()
