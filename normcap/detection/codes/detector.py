"""Barcode and QR Code detection."""

import logging
import os
from collections.abc import Generator

import zxingcpp
from PySide6 import QtGui

from normcap.detection.codes.models import CodeType
from normcap.detection.models import DetectionResult, TextDetector, TextType

logger = logging.getLogger(__name__)


def _image_to_memoryview(image: QtGui.QImage) -> memoryview:
    """Transform Qimage to a bytearray without padding.

    Args:
        image: Input image.

    Returns:
        Memoryview of the image data as 3D array: width x height x RGB.
    """
    image = image.convertToFormat(QtGui.QImage.Format.Format_RGB888)
    ptr = image.constBits()
    bytes_per_line = image.bytesPerLine()  # Includes padding
    width = image.width()
    height = image.height()
    channels = 3  # RGB888 has 3 channels

    # Create a new bytearray to exclude padding
    raw_data = bytearray()
    for y in range(height):
        row_start = y * bytes_per_line
        row_end = row_start + (width * channels)
        raw_data.extend(ptr[row_start:row_end])  # Exclude padding

    return memoryview(raw_data).cast(
        "B", shape=(image.height(), image.width(), channels)
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
    image: memoryview,
) -> Generator[tuple[str, TextType, CodeType], None, None]:
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
    code_types = [r.format for r in results]

    qr_formats = {
        zxingcpp.BarcodeFormat.QRCode,
        zxingcpp.BarcodeFormat.RMQRCode,
        zxingcpp.BarcodeFormat.MicroQRCode,
    }

    logger.info("Found %s codes", len(codes))

    for code, code_format in zip(codes, code_types, strict=True):
        if code_format in qr_formats:
            code_type = CodeType.QR
        elif code_format not in (qr_formats):
            code_type = CodeType.BARCODE
        else:
            raise ValueError()

        text = code.strip()
        text, text_type = _get_text_type_and_transform(text)
        yield text, text_type, code_type


def detect_codes(image: QtGui.QImage) -> list[DetectionResult]:
    """Decode & decode QR and barcodes from image.

    Args:
        image: Input image with potentially one or more barcocdes / QR Codes.

    Returns:
        Result of the detection. If more than one code is detected, the detected values
            are separated by newlines. If no code is detected, None is returned.
    """
    logger.debug("Start QR/Barcode detection")
    # ONHOLD: Switch to using QImage directly, when a new zxingcpp is released
    image_buffer = _image_to_memoryview(image)

    results = []
    for text, text_type, code_type in _detect_codes_via_zxing(image=image_buffer):
        text_detector = TextDetector[code_type.value]
        results.append(
            DetectionResult(text=text, text_type=text_type, detector=text_detector)
        )

    if not results:
        logger.debug("No codes found")

    return results
