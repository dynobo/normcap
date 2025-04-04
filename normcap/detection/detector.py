import logging
import multiprocessing
import time
from typing import Optional

import cv2
import numpy as np
from PySide6 import QtGui

from normcap.detection import codes, ocr
from normcap.detection.models import DetectionResult, TextDetector, TextType
from normcap.gui import system_info

logger = logging.getLogger(__name__)


def _image_to_mat(image: QtGui.QImage) -> np.ndarray:
    ptr = image.constBits()
    arr = np.array(ptr).reshape(image.height(), image.width(), 4)
    return arr[:, :, :3]


def _detect_codes(image: cv2.typing.MatLike) -> Optional[DetectionResult]:
    logger.debug("Start QR/Barcode detection")

    if detections := codes.detector.detect_codes(image=image):
        text, code_text_type, code_type = detections
        logger.debug("Code detection results: %s [%s]", text, code_type)
        text_detector = TextDetector[code_type.value]
        text_type = TextType[code_text_type.value]
        return DetectionResult(text=text, text_type=text_type, detector=text_detector)

    logger.debug("No codes found")
    return None


def _detect_ocr(
    image: cv2.typing.MatLike, language: str, parse: bool
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
    start = time.time()

    mat = _image_to_mat(image=image)
    timeout_codes_s = 60
    timeout_ocr_s = 120
    codes_result = None
    ocr_result = None

    with multiprocessing.Pool(processes=2) as pool:
        future_codes = pool.apply_async(_detect_codes, (mat,)) if detect_codes else None
        future_ocr = pool.apply_async(_detect_ocr, (mat, language, parse_text))

        while True:
            if (
                future_codes
                and future_codes.ready()
                and not future_ocr.ready()
                and (codes_result := future_codes.get(timeout=timeout_codes_s))
            ):
                logger.debug("Stopping OCR early, due to detected QR/Barcode")
                pool.terminate()
                break
            if future_ocr.ready():
                ocr_result = future_ocr.get(timeout=timeout_ocr_s)
                break

    end = time.time()
    logger.info("Detection took %s s", f"{end - start:.4f}")

    detection_result = codes_result or ocr_result
    if detection_result:
        return detection_result

    return DetectionResult(text="", text_type=TextType.NONE, detector=TextDetector.NONE)
