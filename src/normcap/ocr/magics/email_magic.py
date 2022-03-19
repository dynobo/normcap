"""Magic Class to handle e-mail adresses contained in the text."""

import logging
import re

from normcap.ocr.magics.base_magic import BaseMagic
from normcap.ocr.models import OcrResult

logger = logging.getLogger(__name__)


class EmailMagic(BaseMagic):
    """Detect and extract email adress(es) in the OCR results."""

    _emails: list[str] = []

    def score(self, ocr_result: OcrResult) -> float:
        """Calc score based on chars in email adresses vs. overall chars.

        Arguments:
            BaseMagic {class} -- Base class for magics
            capture {Capture} -- NormCap's session data

        Returns:
            float -- score between 0-100 (100 = more likely)
        """
        # Get concatenated lines
        text = ocr_result.text

        # Search email addresses in line
        reg_email = r"[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+"
        self._emails = re.findall(reg_email, text)

        logger.info(
            "%s emails found %s",
            len(self._emails),
            [": " + " ".join(self._emails) if self._emails else ""],
        )

        # Calc chars & ratio
        email_chars = sum(len(e) for e in self._emails)
        all_chars = max([len(text), 1])
        ratio = email_chars / (all_chars * 0.75)

        logger.debug("%s/%s chars in emails. Ratio: %s)", email_chars, all_chars, ratio)
        return round(100 * ratio, 2)

    def transform(self, ocr_result: OcrResult) -> str:
        """Transform to comma separated string of email adresses.

        Other chars not contained in email adresses are discarded.

        Arguments:
            capture {Capture} -- NormCap's session data

        Returns:
            str -- comma separated email adresses
        """
        logger.info("Transform with Email magic")
        return ", ".join(self._emails)
