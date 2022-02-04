import functools
import logging
import traceback
from typing import Union

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
    words = [w for w in words if w["text"].strip()]

    return words


def sanatize_language(
    config_languages: Union[str, list[str]], tesseract_languages: list[str]
) -> list[str]:
    """Retrieve tesseract version number."""
    if isinstance(config_languages, str):
        config_languages = [config_languages]

    set_config_languages = set(config_languages)
    set_tesseract_languages = set(tesseract_languages)
    unavailable_langs = set_config_languages.difference(set_tesseract_languages)
    available_langs = set_config_languages.intersection(set_tesseract_languages)

    if not unavailable_langs:
        return list(set_config_languages)

    logger.warning(
        f"Languages {unavailable_langs} not found. "
        + f"Available on the system are: {set_tesseract_languages}"
    )
    if available_langs:
        logger.warning("Fallback to languages %s", available_langs)
        return list(available_langs)

    fallback_language = set_tesseract_languages.pop()
    logger.warning("Fallback to language %s", fallback_language)
    return list(set([fallback_language]))


def get_tesseract_config(tessdata_path) -> str:
    """Get string with cli args to be passed into tesseract api."""
    return f'--tessdata-dir "{tessdata_path}"' if tessdata_path else ""


@functools.lru_cache()
def get_tesseract_languages(tessdata_path) -> list[str]:
    """Get info abput tesseract setup."""
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
    return version.parse(pytesseract.get_tesseract_version())
