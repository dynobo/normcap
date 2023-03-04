"""Magic Class to handle multi line text selection."""

from normcap.ocr.magics.base_magic import BaseMagic
from normcap.ocr.models import OcrResult


class MultiLineMagic(BaseMagic):
    """Format multi line text."""

    def score(self, ocr_result: OcrResult) -> float:
        # sourcery skip: assign-if-exp, inline-immediately-returned-variable
        """Calc score based on amount of lines and breaks.

        Arguments:
            ocr_result: Recognized text and meta information.

        Returns:
            Score between 0-100 (100 = more likely)
        """
        if (ocr_result.num_lines > 1) and (
            ocr_result.num_blocks == ocr_result.num_pars == 1
        ):
            return 50.0

        return 0

    def transform(self, ocr_result: OcrResult) -> str:
        """Just transform into multiple lines of text.

        Args:
            ocr_result: Recognized text and meta information.

        Returns:
            Lines of text.
        """
        # Just return concatenated text
        return ocr_result.lines
