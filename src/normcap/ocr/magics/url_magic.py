"""Magic to handle URL(s) in selection."""

import logging
import os
import re

from normcap.ocr.magics.base_magic import BaseMagic
from normcap.ocr.models import OcrResult

logger = logging.getLogger(__name__)


class UrlMagic(BaseMagic):
    """Detect and extract urls adress(es) in the OCR results."""

    _urls: list[str] = []
    _manual_correction_table = {
        r"[hn]\w{0,1}t+\w{0,1}ps\s*\:\s*\/+\s*": "https://",
        r"(\w),(\w{1,4}\s*$)": r"\1.\2",  # e.g. gle,com -> gle.com
        r"[wW]{3}\s*\.\s*": "www.",
        r"qithub\.com": "github.com",
        r"[gq]oo[gq]le": "google",
        r"(\s+)([A-Za-z0-9-]+\.[A-Za-z0-9-]+)": r"\1https://\2",  # append https://
    }

    def score(self, ocr_result: OcrResult) -> float:
        """Calculate score based on chars in URLs vs overall chars.

        Arguments:
            BaseMagic {class} -- Base class for magics
            capture {Capture} -- NormCap's session data

        Returns:
            float -- score between 0-100 (100 = more likely)
        """
        # Get concatenated lines
        text = ocr_result.text

        # Remove whitespace between two chars
        # because OCR will often read e.g. "http: //github.com"
        text = re.sub(r":\s+\/", ":/", text)
        # Correct commonly misrecognized parts
        for k, v in self._manual_correction_table.items():
            text = re.sub(k, v, text)

        # Search urls in line
        # (Based on http://www.regexguru.com/2008/11/detecting-urls-in-a-block-of-text/)
        reg_url = (
            r"(?:(?:https?|ftp|file):\/\/|www\.|ftp\.)"  # Prefix
            r"(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[-A-Z0-9+&@#\/%=~_|$?!:,.])*"  # Handle parenthesis
            r"(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[A-Z0-9+&@#\/%=~_|$])"
        )
        self._urls = re.findall(reg_url, text, flags=re.IGNORECASE)
        logger.info(
            "%s URLs found %s",
            len(self._urls),
            [": " + " ".join(self._urls) if self._urls else ""],
        )

        # Calc chars & ratio
        url_chars = sum(len(e) for e in self._urls)
        overall_chars = max([len(text), 1])
        ratio = url_chars / overall_chars
        logger.debug(
            "%s of %s chars in urls (ratio: %s)", url_chars, overall_chars, ratio
        )

        # Map to score
        self._final_score = round(100 * (ratio * 0.85), 2)

        return self._final_score

    def transform(self, ocr_result: OcrResult) -> str:
        """Parse URLs and return as newline separated string.

        Arguments:
            capture {Capture} -- NormCap's session data

        Returns:
            str -- URL(s), separated bye newline
        """
        logger.info("Transform with URL magic")

        # Return as line separated list
        return os.linesep.join(self._urls)
