from typing import Generator

import pytest  # type: ignore
from PySide6 import QtGui

from normcap.gui.downloader_qtnetwork import Downloader as QtNetworkDownloader
from normcap.gui.models import Capture, CaptureMode, Rect


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
