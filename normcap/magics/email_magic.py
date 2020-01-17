"""Magic Class to handle e-mail adresses contained in the text."""

# Default
import re
from typing import List

# Own
from normcap.magics.base_magic import BaseMagic
from normcap.common.data_model import NormcapData


class EmailMagic(BaseMagic):
    """Detect and extract email adress(es) in the OCR results."""

    name = "email"
    _emails: List[str] = []

    def score(self, request: NormcapData) -> float:
        """Calc score based on chars in email adresses vs. overall chars.

        Arguments:
            BaseMagic {class} -- Base class for magics
            request {NormcapData} -- NormCap's session data

        Returns:
            float -- score between 0-100 (100 = more likely)
        """
        # Get concatenated lines
        text = request.text

        # Search email addresses in line
        reg_email = r"[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+"
        self._emails = re.findall(reg_email, text)

        self._logger.info("%s", f"{len(self._emails)} emails found:\n{self._emails}")

        # Calc chars & ratio
        email_chars = sum([len(e) for e in self._emails])
        all_chars = max([len(text), 1])
        ratio = email_chars / (all_chars * 0.85)

        self._logger.info(
            "%s", f"{email_chars}/{all_chars} chars in emails. Ratio: {ratio})"
        )

        # Return final score as 100 * (email_chars / all_chars)
        return round(100 * ratio, 2)

    def transform(self, request: NormcapData) -> str:
        """Transform to comma separated string of email adresses.
        Other chars not contained in email adresses are discarded.

        Arguments:
            request {NormcapData} -- NormCap's session data

        Returns:
            str -- comma separated email adresses
        """
        self._logger.info("Transforming with Email magic...")
        concat_emails = ", ".join(self._emails)
        return concat_emails
