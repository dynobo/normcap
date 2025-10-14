"""Detect OCR tool & language and perform OCR on selected part of image."""

import logging
import sys
import tempfile
import time
from collections.abc import Iterable
from os import PathLike
from pathlib import Path

from PySide6 import QtGui

from normcap.detection.models import DetectionResult, TextDetector, TextType
from normcap.detection.ocr import enhance, tesseract, transformer
from normcap.detection.ocr.models import OEM, PSM, OcrResult, TessArgs

logger = logging.getLogger(__name__)


def _save_image_in_temp_folder(image: QtGui.QImage, postfix: str = "") -> None:
    """For debugging it can be useful to store the cropped image."""
    if logger.getEffectiveLevel() != logging.DEBUG:
        return

    temp_dir = Path(tempfile.gettempdir()) / "normcap"
    temp_dir.mkdir(exist_ok=True)

    now_str = time.strftime("%Y-%m-%d_%H-%M-%S", time.gmtime())
    file_name = f"{now_str}{postfix}.png"

    logger.debug("Save debug image as %s", temp_dir / file_name)
    image.save(str(temp_dir / file_name))


def get_text_from_image(
    languages: str | Iterable[str],
    image: QtGui.QImage,
    tesseract_bin_path: PathLike,
    tessdata_path: PathLike | str | None = None,
    parse: bool = True,
    strip_whitespaces: bool = False,
    resize_factor: float | None = None,
    padding_size: int | None = None,
) -> DetectionResult:
    """Apply OCR on selected image section."""
    image = enhance.preprocess(image, resize_factor=resize_factor, padding=padding_size)
    _save_image_in_temp_folder(image, postfix="_enhanced")

    # TODO: Improve handling of tesseract_cmd and tessdata_path
    if sys.platform == "win32" and tessdata_path:
        tessdata_path = tesseract.get_short_path(str(tessdata_path))

    tess_args = TessArgs(
        tessdata_path=tessdata_path,
        lang=languages if isinstance(languages, str) else "+".join(languages),
        oem=OEM.DEFAULT,
        psm=PSM.AUTO,
    )
    logger.debug(
        "Run Tesseract on image of size %s with args:\n%s",
        (image.width(), image.height()),
        tess_args,
    )
    ocr_result_data = tesseract.perform_ocr(
        tesseract_bin_path=tesseract_bin_path, image=image, args=tess_args.as_list()
    )
    result = OcrResult(tess_args=tess_args, words=ocr_result_data, image=image)
    logger.debug("OCR detections:\n%s", ",\n".join(str(w) for w in result.words))

    if not parse:
        # Even without parsing, apply smart whitespace stripping if enabled
        raw_text = result.text
        if strip_whitespaces and transformer._should_strip_whitespaces(tess_args.lang):
            raw_text = transformer._strip_chinese_whitespaces(raw_text)
        return DetectionResult(
            text=raw_text,
            text_type=TextType.SINGLE_LINE,
            detector=TextDetector.OCR_RAW,
        )

    result = transformer.apply(result, strip_whitespaces=strip_whitespaces)
    logger.debug("Parsed text:\n%s", result.parsed)
    text_type = (
        TextType[result.best_scored_transformer.value]
        if result.best_scored_transformer
        else TextType.SINGLE_LINE
    )
    return DetectionResult(
        text=result.parsed,
        text_type=text_type,
        detector=TextDetector.OCR_PARSED,
    )
