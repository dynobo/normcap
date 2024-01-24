"""Transformer to handle e-mail addresses contained in the text."""

import functools
import logging
import re

from normcap.ocr.structures import OcrResult

logger = logging.getLogger(__name__)


@functools.cache
def _extract_emails(text: str) -> list[str]:
    reg_email = r"""
        [a-zA-Z0-9._-]+  # Valid chars of an email name
        @                # name to domain delimiter
        [a-zA-Z0-9._-]+  # Domain name w/o TLD
        (?:\s{0,1})\.(?:\s{0,1})  # Dot before TLD, potentially with whitespace
                                  # around it, which happens sometimes in OCR.
                                  # The whitespace is not captured.
        [a-zA-Z0-9._-]{2,15}      # TLD, mostly between 2-15 chars.
    """
    return re.findall(reg_email, text, flags=re.X)


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


def score(ocr_result: OcrResult) -> float:
    """Calc score based on chars in email addresses vs. overall chars.

    Arguments:
        ocr_result: Recognized text and meta information.

    Returns:
        score between 0-100 (100 = more likely).
    """
    text = ocr_result.text
    emails = _extract_emails(text)
    logger.info(
        "%s emails found %s", len(emails), f": {' '.join(emails)}" if emails else ""
    )

    # Calc chars & ratio
    email_chars = sum(len(e) for e in emails)
    cleaned_text = _remove_email_names_from_text(emails=emails, text=ocr_result.text)
    count_chars = sum(len(w) for w in cleaned_text.split())
    ratio = min(email_chars / count_chars, 1) if count_chars else 0
    logger.debug("%s/%s (%s) chars in emails", email_chars, count_chars, ratio)
    return round(100 * ratio, 2)


def transform(ocr_result: OcrResult) -> str:
    """Transform to comma separated string of email addresses.

    Other chars not contained in email addresses are discarded.

    Arguments:
        ocr_result: Recognized text and meta information.

    Returns:
        Comma separated email addresses.
    """
    logger.info("Apply email transformer")
    return ", ".join(_extract_emails(ocr_result.text))
