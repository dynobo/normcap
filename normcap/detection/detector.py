import logging
import time
from dataclasses import dataclass
from typing import Optional

from PySide6 import QtGui

from normcap.detection import codes, ocr
from normcap.detection.models import DetectionResult, TextDetector, TextType
from normcap.gui import system_info

logger = logging.getLogger(__name__)


@dataclass
class ImageBytes:
    """Image bytes without padding, but with some metadata."""

    data: bytearray
    height: int
    width: int
    channels: int


def _image_to_memoryview(image: QtGui.QImage) -> memoryview:
    """Transform Qimage to a bytearray without padding.

    Args:
        image: _description_

    Returns:
        _description_
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


def _detect_codes(image: QtGui.QImage) -> Optional[DetectionResult]:
    logger.debug("Start QR/Barcode detection")
    image_buffer = _image_to_memoryview(image)

    if detections := codes.detector.detect_codes(image=image_buffer):
        text, code_text_type, code_type = detections
        logger.debug("Code detection results: %s [%s]", text, code_type)
        text_detector = TextDetector[code_type.value]
        text_type = TextType[code_text_type.value]
        return DetectionResult(text=text, text_type=text_type, detector=text_detector)

    logger.debug("No codes found")
    return None


def _detect_ocr(
    image: QtGui.QImage, language: str, parse: bool
) -> Optional[DetectionResult]:
    logger.debug("Start Text detection")

    ocr_result = ocr.recognize.get_text_from_image(
        tesseract_cmd=ocr.tesseract.get_tesseract_path(
            is_briefcase_package=system_info.is_briefcase_package()
        ),
        languages=language,
        image=image,
        tessdata_path=ocr.tesseract.get_tessdata_path(
            config_directory=system_info.config_directory(),
            is_flatpak_package=system_info.is_flatpak_package(),
            is_briefcase_package=system_info.is_briefcase_package(),
        ),
        parse=parse,
        resize_factor=2,
        padding_size=80,
    )
    if ocr_result.text:
        logger.info("Text from OCR:\n%s", ocr_result.text)
        detector = (
            TextDetector.OCR_PARSED if ocr_result.parsed else TextDetector.OCR_RAW
        )
        # TODO: Performance test OCR + QR vs. OCR only
        # TODO: Better handle missing best_scored_transformer
        text_type = (
            TextType[ocr_result.best_scored_transformer.value]
            if ocr_result.best_scored_transformer
            else TextType.SINGLE_LINE
        )
        # TODO: Test TextType and TextDetector compability of detectors
        return DetectionResult(
            text=ocr_result.text,
            text_type=text_type,
            detector=detector,
        )

    logger.debug("No text found")
    return None


def detect(
    image: QtGui.QImage, language: str, parse_text: bool, detect_codes: bool
) -> DetectionResult:
    ocr_result = None
    codes_result = None

    if detect_codes:
        start_time = time.time()
        codes_result = _detect_codes(image)
        logger.debug("Code detection took %s s", f"{time.time() - start_time:.4f}")

    start_time = time.time()
    ocr_result = _detect_ocr(image, language, parse_text)
    logger.debug("OCR detection took %s s", f"{time.time() - start_time:.4f}")

    detection_result = codes_result or ocr_result
    if detection_result:
        return detection_result

    return DetectionResult(text="", text_type=TextType.NONE, detector=TextDetector.NONE)
