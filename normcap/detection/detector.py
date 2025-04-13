import logging
import time
from dataclasses import dataclass

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


def detect(
    image: QtGui.QImage,
    language: str,
    detect_codes: bool,
    detect_text: bool,
    parse_text: bool,
) -> DetectionResult:
    ocr_result = None
    codes_result = None

    if detect_codes:
        start_time = time.time()
        codes_result = codes.detector.detect_codes(image)
        logger.debug("Code detection took %s s", f"{time.time() - start_time:.4f}.")

    if codes_result:
        logger.debug("Codes detected, skipping OCR.")
        return codes_result

    if detect_text:
        start_time = time.time()
        tessdata_path = ocr.tesseract.get_tessdata_path(
            config_directory=system_info.config_directory(),
            is_flatpak_package=system_info.is_flatpak_package(),
            is_briefcase_package=system_info.is_briefcase_package(),
        )
        tesseract_cmd = ocr.tesseract.get_tesseract_path(
            is_briefcase_package=system_info.is_briefcase_package()
        )
        ocr_result = ocr.recognize.get_text_from_image(
            tesseract_cmd=tesseract_cmd,
            languages=language,
            image=image,
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
