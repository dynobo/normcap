import pytest

from normcap.gui import system_info
from normcap.ocr import utils


def test_get_tesseract_languages():
    tesseract_cmd = system_info.get_tesseract_path()
    tessdata_path = system_info.get_tessdata_path()
    langs = utils.get_tesseract_languages(
        tesseract_cmd=tesseract_cmd, tessdata_path=tessdata_path
    )
    assert langs


def test_get_tesseract_languages_raise_on_wrong_cmd():
    tesseract_cmd = "non-existing-binary"
    tessdata_path = system_info.get_tessdata_path()
    with pytest.raises(RuntimeError, match="Could not run Tesseract binary"):
        _ = utils.get_tesseract_languages(
            tesseract_cmd=tesseract_cmd, tessdata_path=tessdata_path
        )


def test_get_tesseract_languages_raise_on_no_languages(tmp_path):
    tesseract_cmd = system_info.get_tesseract_path()
    tessdata_path = tmp_path
    with pytest.raises(ValueError, match="Could not load any languages"):
        _ = utils.get_tesseract_languages(
            tesseract_cmd=tesseract_cmd, tessdata_path=tessdata_path
        )
