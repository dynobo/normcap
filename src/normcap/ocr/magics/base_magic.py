"""Base class for templating magics."""
import abc

from normcap.ocr.models import OcrResult

# pylint: disable=unused-argument


class BaseMagic(abc.ABC):
    """Base Class to be instantiated."""

    @abc.abstractmethod
    def score(self, ocr_result: OcrResult) -> float:
        """Calculate the score of a magic.

        Score should be between 0-100, where 0 means 'should never be handled
        by this magic' and 100 mean 'should certainly handled by this magic'.

        Arguments:
            capture {Capture} -- Image and meta data on captured section

        Returns:
            float -- score between 0-100 (100 = more likely)
        """

    @abc.abstractmethod
    def transform(self, ocr_result: OcrResult) -> str:
        """Transform detected lineboxes into single(!) string.

        Arguments:
            capture {Capture} -- Image and meta data on captured section

        Returns:
            str -- String to be copied to clipboard
        """
