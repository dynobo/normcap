"""Magic Class to handle paragraph(s) of text."""

from .base_magic import BaseMagic
from normcap.data_model import NormcapData


class ParagraphMagic(BaseMagic):
    """Detect and extract plain text formatted in paragraphs."""

    name = "paragraph"
    
    def score(self, request: NormcapData) -> float:
        """Calc score based on layout of word boxes.

        Arguments:
            BaseMagic {class} -- Base class for magics
            request {NormcapData} -- NormCap's session data

        Returns:
            float -- score between 0-100 (100 = more likely)
        """
        lines = max([len(request.line_boxes), 1])
        self._final_score = 100 - (100 / (lines * 0.9))

        # TODO: Handle Paragraphs
        #  E.g. check for single justified paragraph
        # - Similar right and left bounderies (not for last line)
        # - Similar vertical distance between lines

        return self._final_score

    def transform(self, request: NormcapData) -> str:
        """Transform wordboxes into nicely formatted paragraphs.

        Arguments:
            request {NormcapData} -- NormCap's session data

        Returns:
            str -- Transformed text
        """
        # Just use concatenated text for now.
        # TODO: Maybe remove unnecessary whitespace
        return request.text
