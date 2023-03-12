"""Detect OCR tool & language and perform OCR on selected part of image."""

import logging
from collections.abc import Iterable
from os import PathLike
from typing import Optional, Union

from PIL import Image

from normcap.ocr import enhance, tesseract
from normcap.ocr.magics import Magic
from normcap.ocr.models import OEM, PSM, OcrResult, TessArgs

logger = logging.getLogger(__name__)


def recognize(  # noqa: PLR0913
    tesseract_cmd: PathLike,
    languages: Union[str, Iterable[str]],
    image: Image.Image,
    tessdata_path: Optional[PathLike] = None,
    parse: bool = True,
    resize_factor: Optional[float] = None,
    padding_size: Optional[int] = None,
) -> OcrResult:
    """Apply OCR on selected image section."""
    image = enhance.preprocess(image, resize_factor=resize_factor, padding=padding_size)

    tess_args = TessArgs(
        tessdata_path=tessdata_path,
        lang=languages if isinstance(languages, str) else "+".join(languages),
        oem=OEM.DEFAULT,
        psm=PSM.AUTO_OSD,
    )
    logger.debug(
        "Run Tesseract on image of size %s with args:\n%s", image.size, tess_args
    )
    ocr_result_data = tesseract.perform_ocr(
        cmd=tesseract_cmd, image=image, args=tess_args.as_list()
    )
    result = OcrResult(tess_args=tess_args, words=ocr_result_data, image=image)
    logger.debug("OCR result:\n%s", result)

    if parse:
        result = Magic().apply(result)
        logger.debug("Parsed text:\n%s", result.parsed)

    return result
