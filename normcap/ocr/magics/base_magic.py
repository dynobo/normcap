import abc

from normcap.ocr.models import OcrResult


class BaseMagic(abc.ABC):
    """Provide Base Class to be instantiated."""

    @abc.abstractmethod
    def score(self, ocr_result: OcrResult) -> float:
        """Calculate the score of a magic.

        Score should be between 0-100, where 0 means 'should never be handled
        by this magic' and 100 mean 'should certainly handled by this magic'.

        Args:
            ocr_result: Image and meta data on captured section.

        Returns:
            Score between 0-100 (100 = more likely).
        """

    @abc.abstractmethod
    def transform(self, ocr_result: OcrResult) -> str:
        """Transform detected lineboxes into single(!) string.

        Args:
            ocr_result: Image and meta data on captured section.

        Returns:
            String to be copied to clipboard.
        """
