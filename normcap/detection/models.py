import enum
from typing import NamedTuple


class DetectionMode(enum.Flag):
    TESSERACT = enum.auto()
    CODES = enum.auto()


# ONHOLD: Switch to StrEnum when Python 3.11
class TextType(str, enum.Enum):
    """Describe format/content of the detected text."""

    NONE = "NONE"
    MAIL = "MAIL"
    URL = "URL"
    PHONE_NUMBER = "PHONE_NUMBER"
    SINGLE_LINE = "SINGLE_LINE"
    MULTI_LINE = "MULTI_LINE"
    PARAGRAPH = "PARAGRAPH"
    VEVENT = "VEVENT"
    VCARD = "VCARD"


PlaintextTextTypes = [
    TextType.NONE,
    TextType.SINGLE_LINE,
    TextType.MULTI_LINE,
    TextType.PARAGRAPH,
]


class TextDetector(str, enum.Enum):
    """Specifies the source of the detected text."""

    NONE = "NONE"
    OCR_RAW = "OCR_RAW"
    OCR_PARSED = "OCR_PARSED"
    QR = "QR"
    BARCODE = "BARCODE"
    QR_AND_BARCODE = "QR_AND_BARCODE"


class DetectionResult(NamedTuple):
    text: str
    text_type: TextType
    detector: TextDetector
