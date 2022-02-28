"""Base class for templating magics."""

from normcap.ocr.models import OcrResult

# pylint: disable=unused-argument, no-self-use


class BaseMagic:
    """Base Class to be instantiated."""

    def __init__(self):
        self._final_score = 0  # Initial score

    def score(self, ocr_result: OcrResult) -> float:
        """Calculate the score of a magic.

        Score should be between 0-100, where 0 means 'should never be handled
        by this magic' and 100 mean 'should certainly handled by this magic'.

        Arguments:
            capture {Capture} -- Image and meta data on captured section

        Returns:
            float -- score between 0-100 (100 = more likely)
        """
        return 0.0

    def transform(self, ocr_result: OcrResult) -> str:
        """Transform detected lineboxes into single(!) string.

        Arguments:
            capture {Capture} -- Image and meta data on captured section

        Returns:
            str -- String to be copied to clipboard
        """
        return ""
