"""Detect OCR tool & language and perform OCR on selected part of image."""

import logging
import tempfile
import time
from collections.abc import Iterable
from os import PathLike
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np

from normcap.detection.ocr import enhance, tesseract, transformer
from normcap.detection.ocr.models import OEM, PSM, OcrResult, TessArgs

logger = logging.getLogger(__name__)


def _save_image_in_temp_folder(image: np.ndarray, postfix: str = "") -> None:
    """For debugging it can be useful to store the cropped image."""
    if logger.getEffectiveLevel() != logging.DEBUG:
        return

    temp_dir = Path(tempfile.gettempdir()) / "normcap"
    temp_dir.mkdir(exist_ok=True)

    now_str = time.strftime("%Y-%m-%d_%H-%M-%S", time.gmtime())
    file_name = f"{now_str}{postfix}.png"

    logger.debug("Save debug image as %s", temp_dir / file_name)
    cv2.imwrite(str(temp_dir / file_name), image)


def get_text_from_image(  # noqa: PLR0913
    tesseract_cmd: PathLike,
    languages: Union[str, Iterable[str]],
    image: np.ndarray,
    tessdata_path: Optional[PathLike] = None,
    parse: bool = True,
    resize_factor: Optional[float] = None,
    padding_size: Optional[int] = None,
) -> OcrResult:
    """Apply OCR on selected image section."""
    image = enhance.preprocess(image, resize_factor=resize_factor, padding=padding_size)
    _save_image_in_temp_folder(image, postfix="_enhanced")

    tess_args = TessArgs(
        tessdata_path=tessdata_path,
        lang=languages if isinstance(languages, str) else "+".join(languages),
        oem=OEM.DEFAULT,
        psm=PSM.AUTO,
    )
    logger.debug(
        "Run Tesseract on image of size %s with args:\n%s",
        image.shape[:2],
        tess_args,
    )
    ocr_result_data = tesseract.perform_ocr(
        cmd=tesseract_cmd, image=image, args=tess_args.as_list()
    )
    result = OcrResult(tess_args=tess_args, words=ocr_result_data, image=image)
    logger.debug("OCR detections:\n%s", ",\n".join(str(w) for w in result.words))

    if parse:
        result = transformer.apply(result)
        logger.debug("Parsed text:\n%s", result.parsed)

    return result
