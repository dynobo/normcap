"""Detect OCR tool & language and perform OCR on selected part of image."""

import logging
import tempfile
from typing import Union

import pytesseract  # type: ignore
from PySide6 import QtGui

from normcap.ocr import utils
from normcap.ocr.magics import magic
from normcap.ocr.models import OEM, PSM, OcrResult, TessArgs

logger = logging.getLogger(__name__)


def recognize(
    languages: Union[str, list[str]],
    image: QtGui.QImage,
    tessdata_path=None,
    parse: bool = True,
) -> OcrResult:
    """Apply OCR on selected image section."""
    languages = utils.sanatize_language(
        languages, utils.get_tesseract_languages(tessdata_path)
    )
    tess_args = TessArgs(
        path=tessdata_path,
        lang=languages,
        oem=OEM.LSTM_ONLY,
        psm=PSM.AUTO_OSD,
        version=utils.get_tesseract_version,  # type: ignore
    )
    logger.debug("Init tesseract with args: %s", tess_args)

    with tempfile.NamedTemporaryFile(delete=False) as fp:
        image.save(fp.name + ".png")
        tsv_data = pytesseract.image_to_data(
            fp.name + ".png",
            lang="+".join(tess_args.lang),
            output_type=pytesseract.Output.DICT,
            timeout=30,
            config=utils.get_tesseract_config(tessdata_path),
        )

    result = OcrResult(tess_args=tess_args, words=utils.tsv_to_list_of_dicts(tsv_data))
    logger.info("Mean Conf: %s", result.mean_conf)

    if parse:
        result = magic.apply_magic(result)

    return result
