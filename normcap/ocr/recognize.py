"""Detect OCR tool & language and perform OCR on selected part of image."""

import logging
from os import PathLike
from typing import Iterable, Optional, Union

from PIL import Image
from pytesseract import pytesseract

from normcap.ocr import enhance, utils
from normcap.ocr.magics import Magic
from normcap.ocr.models import OEM, PSM, OcrResult, TessArgs

logger = logging.getLogger(__name__)


def recognize(
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
        path=tessdata_path,
        lang=languages if isinstance(languages, str) else "+".join(languages),
        oem=OEM.DEFAULT,
        psm=PSM.AUTO_OSD,
        version=utils.get_tesseract_version(tesseract_cmd),  # type: ignore
        # For the type ignore, see: https://github.com/python/mypy/issues/5107
    )
    logger.debug(
        "Run Tesseract on image of size %s with args:\n%s", image.size, tess_args
    )

    pytesseract.tesseract_cmd = str(tesseract_cmd)
    tsv_data = pytesseract.image_to_data(
        image,
        lang=tess_args.lang,
        output_type=pytesseract.Output.DICT,
        timeout=30,
        config=tess_args.to_config_str(),
    )

    result = OcrResult(
        tess_args=tess_args, words=utils.tsv_to_list_of_dicts(tsv_data), image=image
    )
    logger.debug("OCR result:\n%s", result)

    if parse:
        result = Magic().apply(result)
        logger.debug("Parsed text:\n%s", result.parsed)

    return result
