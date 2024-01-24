"""Detect OCR tool & language and perform OCR on selected part of image."""

import logging
from collections.abc import Iterable
from os import PathLike
from typing import Optional, Union

from PySide6.QtGui import QImage

from normcap.ocr import enhance, tesseract, transformer
from normcap.ocr.structures import OEM, PSM, OcrResult, TessArgs

logger = logging.getLogger(__name__)


def get_text_from_image(  # noqa: PLR0913
    tesseract_cmd: PathLike,
    languages: Union[str, Iterable[str]],
    image: QImage,
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
        psm=PSM.AUTO,
    )
    logger.debug(
        "Run Tesseract on image of size %s with args:\n%s",
        image.size().toTuple(),
        tess_args,
    )
    ocr_result_data = tesseract.perform_ocr(
        cmd=tesseract_cmd, image=image, args=tess_args.as_list()
    )
    result = OcrResult(tess_args=tess_args, words=ocr_result_data, image=image)
    logger.debug("OCR result:\n%s", result)

    if parse:
        result = transformer.apply(result)
        logger.debug("Parsed text:\n%s", result.parsed)

    return result
