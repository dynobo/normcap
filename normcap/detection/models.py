import enum
from typing import NamedTuple


class TextType(str, enum.Enum):
    """Describe format/content of the detected text."""

    NONE = "NONE"
    MAIL = "MAIL"
    URL = "URL"
    PHONE_NUMBER = "PHONE_NUMBER"
    SINGLE_LINE = "SINGLE_LINE"
    MULTI_LINE = "MULTI_LINE"
    PARAGRAPH = "PARAGRAPH"


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
