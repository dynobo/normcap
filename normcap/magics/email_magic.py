"""Magic Class to handle e-mail adresses contained in the text."""

# Default
import re
import webbrowser

# Own
from magics.base_magic import BaseMagic
from data_model import NormcapData


class EmailMagic(BaseMagic):
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
        self.emails = re.findall(reg_email, text)

        self._logger.info(f"{len(self.emails)} emails found:\n{self.emails}")

        # Calc chars & ratio
        email_chars = sum([len(e) for e in self.emails])
        all_chars = len(text)
        ratio = email_chars / all_chars

        self._logger.info(f"{email_chars}/{all_chars} chars in emails. Ratio: {ratio})")

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
        concat_emails = ", ".join(self.emails)
        return concat_emails

    def trigger(self, request: NormcapData):
        """Open adresses as mailto: link.

        Arguments:
            request {NormcapData} -- NormCap's session data
        """
        self._logger.info("Open mailto link...")
        webbrowser.open(f"mailto:{request.transformed}")
