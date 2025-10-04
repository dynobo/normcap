"""Transformer to handle paragraph(s) of text."""

import os

from normcap.detection.ocr.models import OcrResult, TransformerProtocol


class ParagraphTransformer(TransformerProtocol):
    @staticmethod
    def score(ocr_result: OcrResult) -> float:
        """Calc score based on layout of amount of paragraphs and blocks.

        Arg:
            ocr_result: Recognized text and meta information.

        Returns:
            Score between 0-100 (100 = more likely).
        """
        breaks = max(1, ocr_result.num_blocks + ocr_result.num_pars - 1)
        return 100 - (100 / breaks)

    @staticmethod
    def transform(ocr_result: OcrResult) -> list[str]:
        """Transform word-boxes into nicely formatted paragraphs.

        Args:
            ocr_result: Recognized text and meta information.

        Returns:
            Transformed text.
        """
        # ignore linebreaks within paragraphs:
        return [ocr_result.add_linebreaks(block_sep=os.linesep, line_sep=" ")]
