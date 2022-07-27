from pathlib import Path
from typing import Generator

import pytest
from packaging import version
from PySide6 import QtGui

from normcap.gui.downloader_qtnetwork import Downloader as QtNetworkDownloader
from normcap.gui.models import Capture, CaptureMode, Rect
from normcap.ocr.models import OcrResult, TessArgs
from normcap.utils import create_argparser


def pytest_configure(config):
    config.addinivalue_line("markers", "skip_on_gh: do not run during CI/CD on github")


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
def downloader() -> Generator[QtNetworkDownloader, None, None]:
    yield QtNetworkDownloader()


@pytest.fixture(scope="session")
def ocr_result() -> OcrResult:
    """Create argparser and provide its default values."""
    return OcrResult(
        tess_args=TessArgs(
            path=Path(), lang="eng", oem=2, psm=2, version=version.parse("5.0.0")
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


@pytest.fixture(scope="session")
def argparser_defaults():
    argparser = create_argparser()
    return vars(argparser.parse_args([]))
