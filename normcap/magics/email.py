# Default
import re
import webbrowser

# Own
from magics.base_magic import BaseMagic


class EmailMagic(BaseMagic):
    def score(self, request):
        # Get concatenated lines
        text = request.text

        # Search email addresses in line
        reg_email = r"[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+"
        self.emails = re.findall(reg_email, text)
        self._logger.info(f"{len(self.emails)} emails found:\n{self.emails}")

        # Calc chars & ratio
        email_chars = sum([len(e) for e in self.emails])
        overall_chars = len(text)
        ratio = email_chars / overall_chars
        self._logger.info(
            f"{email_chars} of {overall_chars} chars in emails (ratio: {ratio})"
        )

        # Map to score
        self._final_score = round(100 * ratio, 2)

        return self._final_score

    def transform(self, request):
        self._logger.info("Transforming with Email magic...")
        concat_emails = ", ".join(self.emails)
        return concat_emails

    def trigger(self, request):
        self._logger.info("Open mailto link...")
        webbrowser.open(f"mailto:{request.transformed}")
        return
