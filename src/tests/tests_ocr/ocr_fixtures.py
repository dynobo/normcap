from pathlib import Path

import pytest  # type: ignore
from packaging import version
from PySide6 import QtGui

from normcap.ocr.models import OcrResult, TessArgs

# Specific settings for pytest
# pylint: disable=redefined-outer-name,protected-access,unused-argument


@pytest.fixture(scope="session")
def ocr_result() -> OcrResult:
    """Create argparser and provide its default values."""
    return OcrResult(
        tess_args=TessArgs(
            path=Path(), lang=["eng"], oem=2, psm=2, version=version.parse("5.0.0")
        ),
        image=QtGui.QImage(),
        magic_scores={},
        transformed="",
        words=[
            {
                "level": 1,
                "page_num": 1,
                "block_num": 1,
                "par_num": 1,
                "line_num": 1,
                "word_num": 1,
                "left": 5,
                "top": 0,
                "width": 55,
                "height": 36,
                "conf": 20,
                "text": "one",
            },
            {
                "level": 1,
                "page_num": 1,
                "block_num": 1,
                "par_num": 2,
                "line_num": 1,
                "word_num": 2,
                "left": 5,
                "top": 0,
                "width": 55,
                "height": 36,
                "conf": 40,
                "text": "two",
            },
            {
                "level": 1,
                "page_num": 1,
                "block_num": 2,
                "par_num": 3,
                "line_num": 3,
                "word_num": 3,
                "left": 5,
                "top": 0,
                "width": 55,
                "height": 36,
                "conf": 30,
                "text": "three",
            },
        ],
    )
