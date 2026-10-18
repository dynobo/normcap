"""Barcode and QR Code detection."""

import logging
import os
from collections.abc import Generator

import zxingcpp
from PySide6 import QtGui

from normcap.detection.codes.models import CodeType
from normcap.detection.models import DetectionResult, TextDetector, TextType

logger = logging.getLogger(__name__)

# QImage formats which zxingcpp can read directly. Everything else has to be converted
# beforehand, because zxingcpp's own fallback calls `convertToFormat(24)` with a plain
# int where PySide6 requires a `QImage.Format` enum, and therefore always raises.
_SUPPORTED_IMAGE_FORMATS = frozenset(
    {
        QtGui.QImage.Format.Format_ARGB32,
        QtGui.QImage.Format.Format_BGR888,
        QtGui.QImage.Format.Format_Grayscale8,
        QtGui.QImage.Format.Format_RGBA8888,
        QtGui.QImage.Format.Format_RGB32,
        QtGui.QImage.Format.Format_RGB888,
    }
)


def _get_text_type_and_transform(text: str) -> tuple[str, TextType]:
    """Estimate the type of text based on the content."""
    if text.startswith("https://") or text.startswith("http://"):
        text_type = TextType.URL
    elif text.startswith("tel:"):
        text = text.removeprefix("tel:")
        text_type = TextType.PHONE_NUMBER
    elif text.startswith("mailto:"):
        text = text.removeprefix("mailto:")
        text_type = TextType.MAIL
    elif text.startswith("BEGIN:VCARD") and text.endswith("END:VCARD"):
        text_type = TextType.VCARD
    elif text.startswith("BEGIN:VEVENT") and text.endswith("END:VEVENT"):
        text_type = TextType.VEVENT
    elif os.linesep + os.linesep in text:
        text_type = TextType.PARAGRAPH
    elif os.linesep in text:
        text_type = TextType.MULTI_LINE
    else:
        text_type = TextType.SINGLE_LINE

    return text, text_type


def _detect_codes_via_zxing(
    image: QtGui.QImage,
) -> Generator[tuple[str, TextType, CodeType], None, None]:
    """Decode QR and barcodes from image.

    Args:
        image: Input image.

    Yields:
        Detected text, type of text and type of code.
    """
    logger.info("Detect Barcodes and QR Codes")

    if image.format() not in _SUPPORTED_IMAGE_FORMATS:
        logger.debug("Convert %s to RGB888 for zxingcpp", image.format())
        image = image.convertToFormat(QtGui.QImage.Format.Format_RGB888)

    results = zxingcpp.read_barcodes(image)

    if not results:
        return

    qr_formats = {
        zxingcpp.BarcodeFormat.QRCode,
        zxingcpp.BarcodeFormat.RMQRCode,
        zxingcpp.BarcodeFormat.MicroQRCode,
    }

    logger.info("Found %s codes", len(results))

    for result in results:
        if not result.valid:
            logger.warning("Invalid %s result: %s", result.format, result.error)
            continue

        if not result.text:
            logger.debug("Skip %s result without text", result.format)
            continue

        code_type = CodeType.QR if result.format in qr_formats else CodeType.BARCODE

        text, text_type = _get_text_type_and_transform(result.text.strip())
        yield text, text_type, code_type


def detect_codes(image: QtGui.QImage) -> list[DetectionResult]:
    """Detect & decode QR and barcodes from image.

    Args:
        image: Input image with potentially one or more barcodes / QR Codes.

    Returns:
        Result of the detection. If more than one code is detected, the detected values
            are separated by newlines. An empty list if no code is detected.
    """
    logger.debug("Start QR/Barcode detection")

    results = []
    for text, text_type, code_type in _detect_codes_via_zxing(image=image):
        text_detector = TextDetector[code_type.value]
        results.append(
            DetectionResult(text=text, text_type=text_type, detector=text_detector)
        )

    if not results:
        logger.debug("No codes found")

    return results
