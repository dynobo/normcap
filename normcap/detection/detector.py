import logging
import time
from pathlib import Path

from PySide6 import QtGui

from normcap.detection import codes, ocr
from normcap.detection.models import (
    DetectionMode,
    DetectionResult,
    TextDetector,
    TextType,
)

logger = logging.getLogger(__name__)


def detect(
    image: QtGui.QImage,
    tesseract_bin_path: Path,
    tessdata_path: Path | None,
    language: str,
    detect_mode: DetectionMode,
    parse_text: bool,
) -> DetectionResult:
    ocr_result = None
    codes_result = None

    if DetectionMode.CODES in detect_mode:
        start_time = time.time()
        codes_result = codes.detector.detect_codes(image)
        logger.debug("Code detection took %s s", f"{time.time() - start_time:.4f}.")

    if codes_result:
        logger.debug("Codes detected, skipping OCR.")
        return codes_result

    if DetectionMode.TESSERACT in detect_mode:
        start_time = time.time()
        ocr_result = ocr.recognize.get_text_from_image(
            languages=language,
            image=image,
            tesseract_bin_path=tesseract_bin_path,
            tessdata_path=tessdata_path,
            parse=parse_text,
            resize_factor=2,
            padding_size=80,
        )
        logger.debug("OCR detection took %s s", f"{time.time() - start_time:.4f}.")

    if ocr_result:
        logger.debug("Text detected.")
        return ocr_result

    logger.debug("No codes or text found!")
    return DetectionResult(text="", text_type=TextType.NONE, detector=TextDetector.NONE)
