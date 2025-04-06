"""Barcode and QR Code detection."""

import logging
import os
from pathlib import Path
from typing import Optional

import zxingcpp

from normcap import resources
from normcap.detection.codes.models import CodeType, TextType

logger = logging.getLogger(__name__)

model_path = Path(resources.__file__).parent / "qr"

qr_formats = {
    zxingcpp.BarcodeFormat.QRCode,
    zxingcpp.BarcodeFormat.RMQRCode,
    zxingcpp.BarcodeFormat.MicroQRCode,
}


def _detect_code_zxingcpp(mv: memoryview) -> list[str]:
    """Detect QR codes using ZXing C++.

    Similar accuracy to the default OpenCV model but faster on large images.
    """
    results = zxingcpp.read_barcodes(mv)
    return [result.text for result in results if result.text]


def _get_text_type(text: str) -> TextType:
    if text.startswith("http"):
        return TextType.URL
    if text.startswith("tel:"):
        return TextType.PHONE_NUMBER
    if text.startswith("mailto:"):
        return TextType.MAIL
    if os.sep + os.sep in text:
        return TextType.PARAGRAPH
    if os.sep in text:
        return TextType.MULTI_LINE
    return TextType.SINGLE_LINE


def detect_codes(image: memoryview) -> Optional[tuple[str, TextType, CodeType]]:
    """Decode QR and barcodes from image.

    Args:
        image: Input image.

    Returns:
        URL(s), separated bye newline
    """
    logger.info("Detect Barcodes and QR Codes")

    results = zxingcpp.read_barcodes(image)

    if not results:
        return None

    codes = [result.text for result in results if result.text]
    code_types = {r.format for r in results}

    if code_types.issubset(qr_formats):
        code_type = CodeType.QR
    elif not code_types.intersection(qr_formats):
        code_type = CodeType.BARCODE
    else:
        code_type = CodeType.QR_AND_BARCODE

    logger.info("Found %s codes", len(codes))

    if len(codes) == 1:
        text = codes[0]
        return text, _get_text_type(text), code_type

    return os.linesep.join(codes), TextType.MULTI_LINE, code_type
