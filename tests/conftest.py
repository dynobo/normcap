import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from PIL import Image
from PySide6 import QtCore, QtGui

from normcap.gui.models import Capture, CaptureMode, Rect
from normcap.ocr.models import OcrResult, TessArgs
from normcap.utils import create_argparser


@pytest.fixture()
def temp_settings():
    settings = QtCore.QSettings("dynobo", "normcap_tests")
    yield settings
    settings.remove("")


@pytest.fixture()
def dbus_portal():
    try:
        from normcap.screengrab import dbus_portal

        return dbus_portal
    except ImportError as e:
        if sys.platform != "linux":
            pytest.xfail(f"Import error: {e}")


@pytest.fixture()
def capture() -> Generator[Capture, None, None]:
    """Create argparser and provide its default values."""
    image = QtGui.QImage(200, 300, QtGui.QImage.Format.Format_RGB32)
    image.fill(QtGui.QColor("#ff0000"))

    yield Capture(
        mode=CaptureMode.PARSE,
        rect=Rect(20, 30, 220, 330),
        ocr_text="one two three",
        ocr_applied_magic="",
        image=image,
    )


@pytest.fixture()
def ocr_result() -> OcrResult:
    """Create argparser and provide its default values."""
    return OcrResult(
        tess_args=TessArgs(path=Path(), lang="eng", oem=2, psm=2, version="5.0.0"),
        image=Image.Image(),
        magic_scores={},
        parsed="",
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


@pytest.fixture()
def argparser_defaults():
    argparser = create_argparser()
    return vars(argparser.parse_args([]))
