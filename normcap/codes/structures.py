import enum


class Transformer(str, enum.Enum):
    QR = "QR"
    BARCODE = "BARCODE"
    QR_AND_BARCODE = "QR_AND_BARCODE"
