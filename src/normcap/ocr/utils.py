import functools
import logging
import os
import traceback

import pytesseract
from packaging import version

logger = logging.getLogger(__name__)


def tsv_to_list_of_dicts(tsv_data: dict) -> list[dict]:
    """Transpose tsv dict from k:list[v] to list[Dict[k:v]]."""
    words: list[dict] = [{} for _ in tsv_data["level"]]
    for k, values in tsv_data.items():
        for idx, v in enumerate(values):
            words[idx][k] = v

    # Filter empty words
    return [w for w in words if w["text"].strip()]


def get_tesseract_config(tessdata_path) -> str:
    """Get string with cli args to be passed into tesseract api."""
    return f'--tessdata-dir "{tessdata_path}"' if tessdata_path else ""


def configure_tesseract_binary():
    """Override tesseract command and version, if applicable."""
    if tesseract_cmd := os.environ.get("TESSERACT_CMD", ""):
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    if tesseract_version := os.environ.get("TESSERACT_VERSION", ""):

        def _patched_get_tesseract_version():
            return version.Version(tesseract_version)

        pytesseract.get_tesseract_version = _patched_get_tesseract_version
        pytesseract.pytesseract.get_tesseract_version = _patched_get_tesseract_version


@functools.lru_cache()
def get_tesseract_languages(tessdata_path) -> list[str]:
    """Get info abput tesseract setup."""
    configure_tesseract_binary()

    try:
        languages = sorted(
            pytesseract.get_languages(config=get_tesseract_config(tessdata_path))
        )
    except RuntimeError as e:
        traceback.print_tb(e.__traceback__)
        raise RuntimeError(
            "Couldn't determine Tesseract information. If you pip installed NormCap "
            + "make sure Tesseract is installed and configured correctly."
        ) from e

    if not languages:
        raise ValueError(
            "Could not load any languages for tesseract. "
            + "On Windows, make sure that TESSDATA_PREFIX environment variable is set. "
            + "On Linux/MacOS see if 'tesseract --list-langs' work is the command line."
        )

    return languages


@functools.lru_cache()
def get_tesseract_version() -> version.Version:
    """Get info abput tesseract setup."""
    tesseract_version = str(pytesseract.get_tesseract_version()).splitlines()[0]
    return version.parse(tesseract_version)
