"""Magic Class to handle e-mail addresses contained in the text."""

import functools
import logging
import re

from normcap.ocr.magics.base_magic import BaseMagic
from normcap.ocr.models import OcrResult

logger = logging.getLogger(__name__)


class EmailMagic(BaseMagic):
    """Detect and extract email address(es) in the OCR results."""

    @staticmethod
    @functools.cache
    def _extract_emails(text: str) -> list[str]:
        reg_email = r"[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.(?:\s{1,0})[a-zA-Z0-9._-]+"
        return re.findall(reg_email, text)

    @staticmethod
    def _remove_email_names_from_text(emails: list[str], text: str) -> str:
        """Remove names in emails from text.

        In many mail programs, email addresses are displayed together with the
        person names, e.g.: John Doe <john.doe@domain.com>;
        This function heuristically removes those names from the text to achieve
        a more precise score.
        """
        for email in emails:
            components = email.split("@")
            if len(components) > 1:
                for name in components[0].split("."):
                    text = re.sub(
                        r"(?i)(^|\s)" + re.escape(name) + r"(\s|$)", r"\1\2", text
                    )
        text = re.sub(r"(>|<|;|,)", " ", text)
        return re.sub(r"\s+", " ", text)

    def score(self, ocr_result: OcrResult) -> float:
        """Calc score based on chars in email addresses vs. overall chars.

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
        cleaned_text = self._remove_email_names_from_text(
            emails=emails, text=ocr_result.text
        )
        count_chars = sum(len(w) for w in cleaned_text.split())
        ratio = min(email_chars / count_chars, 1) if count_chars else 0
        logger.debug("%s/%s (%s) chars in emails", email_chars, count_chars, ratio)
        return round(100 * ratio, 2)

    def transform(self, ocr_result: OcrResult) -> str:
        """Transform to comma separated string of email addresses.

        Other chars not contained in email addresses are discarded.

        Arguments:
            ocr_result: Recognized text and meta information.

        Returns:
            Comma separated email addresses.
        """
        logger.info("Transform with Email magic")
        return ", ".join(self._extract_emails(ocr_result.text))
