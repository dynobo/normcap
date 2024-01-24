"""Transformer to handle URL(s) in selection."""

import functools
import logging
import os
import re

from normcap.ocr.structures import OcrResult
from normcap.ocr.transformers import url_tlds

logger = logging.getLogger(__name__)


def _has_valid_tld(url: str) -> bool:
    """Check if hostname ends with a valid TLD."""
    match = re.search(r"(?:\.)([a-zA-Z]+)(?:\/|$)", url, re.IGNORECASE)
    tld = match.group(1) if match else ""
    return tld.upper() in url_tlds.TLDS


@functools.cache
def _extract_urls(text: str) -> list[str]:
    manual_correction_table = {
        r"[hn]\w{0,1}t+\w{0,1}ps\s*\:\s*\/+\s*": "https://",
        r"(\w),(\w{1,4}\s*$)": r"\1.\2",  # e.g. gle,com -> gle.com
        r"(https?:\/\/)*[wW]{3}\s*\.\s*": "https://www.",
        r"qithub\.com": "github.com",
        r"[gq]oo[gq]le": "google",
        r"(\s+)([A-Za-z0-9-]{4,}\.[A-Za-z0-9-]{2,4})": r"\1https://\2",  # add proto
    }
    # Remove whitespace between two chars
    # because OCR will often read e.g. "http: //github.com"
    text = re.sub(r":\s+\/", ":/", text)
    # Correct commonly unrecognized parts
    for k, v in manual_correction_table.items():
        text = re.sub(k, v, text)

    # Search urls in line
    # (Based on http://www.regexguru.com/2008/11/detecting-urls-in-a-block-of-text/)
    reg_url = (
        r"(?:(?:https?|ftp|file):\/\/|www\.|ftp\.)"  # Prefix
        r"(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[-A-Z0-9+&@#\/%=~_|$?!:,.])*"
        r"(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[A-Z0-9+&@#\/%=~_|$])"
    )
    all_urls = re.findall(reg_url, text, flags=re.IGNORECASE)
    return [url for url in all_urls if _has_valid_tld(url=url)]


def score(ocr_result: OcrResult) -> float:
    """Calculate score based on chars in URLs vs overall chars.

    Args:
        ocr_result: Recognized text and meta information.

    Returns:
        score between 0-100 (100 = more likely)
    """
    text = ocr_result.text
    urls = _extract_urls(text)
    logger.info("%s URLs found %s", len(urls), ": " + " ".join(urls) if urls else "")

    # Calc chars & ratio
    url_chars = sum(len(e) for e in urls)
    all_chars = max([len(text), 1])
    ratio = url_chars / all_chars
    logger.debug("%s/%s (%s) chars in urls", url_chars, all_chars, ratio)

    return round(100 * min(ratio * 0.85, 1), 2)


def transform(ocr_result: OcrResult) -> str:
    """Parse URLs and return as newline separated string.

    Args:
        ocr_result: Recognized text and meta information.

    Returns:
        URL(s), separated bye newline
    """
    logger.info("Apply url transformer")
    urls = _extract_urls(ocr_result.text)

    return os.linesep.join(urls)
