import enum


class CodeType(str, enum.Enum):
    NONE = "NONE"
    QR = "QR"
    BARCODE = "BARCODE"


class TextType(str, enum.Enum):
    """Describe format/content of the detected text."""

    NONE = "NONE"
    MAIL = "MAIL"
    URL = "URL"
    PHONE_NUMBER = "PHONE_NUMBER"
    SINGLE_LINE = "SINGLE_LINE"
    MULTI_LINE = "MULTI_LINE"
    PARAGRAPH = "PARAGRAPH"
