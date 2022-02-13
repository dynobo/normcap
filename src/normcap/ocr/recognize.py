"""Detect OCR tool & language and perform OCR on selected part of image."""

import logging
import tempfile
from typing import Optional, Union

import pytesseract  # type: ignore
from PIL import Image

from normcap.ocr import utils
from normcap.ocr.enhance import add_padding, resize_image
from normcap.ocr.magics import magic
from normcap.ocr.models import OEM, PSM, OcrResult, TessArgs

logger = logging.getLogger(__name__)


def recognize(
    languages: Union[str, list[str]],
    image: Image.Image,
    tessdata_path=None,
    parse: bool = True,
    resize_factor: Optional[float] = None,
    padding_size: Optional[int] = None,
) -> OcrResult:
    """Apply OCR on selected image section."""
    utils.configure_tesseract_binary()

    if resize_factor:
        image = resize_image(image, factor=resize_factor)
    if padding_size:
        image = add_padding(image, padding=padding_size)

    tess_args = TessArgs(
        path=tessdata_path,
        lang=languages if isinstance(languages, str) else "+".join(languages),
        oem=OEM.TESSERACT_LSTM_COMBINED,
        psm=PSM.AUTO_OSD,
        version=utils.get_tesseract_version(),
    )
    logger.debug("Init tesseract with args: %s", tess_args)
    logger.debug("Image size: %s", image.size)

    with tempfile.NamedTemporaryFile(delete=False) as fp:
        image.save(f"{fp.name}.png")
        tsv_data = pytesseract.image_to_data(
            f"{fp.name}.png",
            lang=tess_args.lang,
            output_type=pytesseract.Output.DICT,
            timeout=30,
            config=utils.get_tesseract_config(tessdata_path),
        )

    result = OcrResult(
        tess_args=tess_args, words=utils.tsv_to_list_of_dicts(tsv_data), image=image
    )
    logger.debug("OCR result: %s", result)

    if parse:
        result = magic.apply_magic(result)
        logger.debug("Transformed text: %s", result.transformed)

    return result
