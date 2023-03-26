"""Magic Class to handle e-mail adresses contained in the text."""

import functools
import logging
import re

from normcap.ocr.magics.base_magic import BaseMagic
from normcap.ocr.models import OcrResult

logger = logging.getLogger(__name__)


class EmailMagic(BaseMagic):
    """Detect and extract email adress(es) in the OCR results."""

    @staticmethod
    @functools.cache
    def _extract_emails(text: str) -> list[str]:
        reg_email = r"[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+"
        return re.findall(reg_email, text)

    def score(self, ocr_result: OcrResult) -> float:
        """Calc score based on chars in email adresses vs. overall chars.

        Arguments:
            ocr_result: Recognized text and meta information.

        Returns:
            score between 0-100 (100 = more likely).
        """
        text = ocr_result.text
        emails = self._extract_emails(text)
        logger.info(
            "%s emails found %s", len(emails), f": {' '.join(emails)}" if emails else ""
        )

        # Calc chars & ratio
        email_chars = sum(len(e) for e in emails)
        count_chars = ocr_result.num_chars
        ratio = min(email_chars / count_chars, 1) if count_chars else 0
        logger.debug("%s/%s (%s) chars in emails", email_chars, count_chars, ratio)
        return round(100 * ratio, 2)

    def transform(self, ocr_result: OcrResult) -> str:
        """Transform to comma separated string of email adresses.

        Other chars not contained in email adresses are discarded.

        Arguments:
            ocr_result: Recognized text and meta information.

        Returns:
            Comma separated email adresses.
        """
        logger.info("Transform with Email magic")
        return ", ".join(self._extract_emails(ocr_result.text))
