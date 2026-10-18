import enum


class CodeType(enum.StrEnum):
    NONE = "NONE"
    QR = "QR"
    BARCODE = "BARCODE"


class TextType(enum.StrEnum):
    """Describe format/content of the detected text."""

    NONE = "NONE"
    MAIL = "MAIL"
    URL = "URL"
    PHONE_NUMBER = "PHONE_NUMBER"
    SINGLE_LINE = "SINGLE_LINE"
    MULTI_LINE = "MULTI_LINE"
    PARAGRAPH = "PARAGRAPH"
