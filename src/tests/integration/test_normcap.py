import logging
from pathlib import Path

import Levenshtein
import pytest
from PySide6 import QtCore, QtGui

import normcap
from normcap.args import create_argparser
from normcap.gui.tray import SystemTray

from .testcases.data import TESTCASES

logger = logging.getLogger(__name__)

# Specific settings for pytest
# pylint: disable=redefined-outer-name,protected-access,unused-argument


@pytest.mark.parametrize(
    "data",
    TESTCASES,
)
def test_app(monkeypatch, qtbot, qapp, xvfb, data):
    """Tests complete OCR workflow."""
    screen_rect = qapp.primaryScreen().size()
    if screen_rect.width() != 1920 or screen_rect.height() != 1080:
        pytest.xfail("Skipped due to wrong screen resolution.")

    test_file = Path(__file__).parent / "testcases" / data["image"]
    test_image = QtGui.QImage(test_file.absolute())

    monkeypatch.setattr(normcap.gui.tray, "grab_screens", lambda: [test_image])
    args = create_argparser().parse_args(["--language=eng", "--mode=parse"])
    tray = SystemTray(None, vars(args))
    tray.show()

    window = tray.windows[0]
    qtbot.mousePress(window, QtCore.Qt.LeftButton, pos=QtCore.QPoint(*data["tl"]))
    qtbot.mouseMove(window, pos=QtCore.QPoint(*data["br"]))
    qtbot.mouseRelease(window, QtCore.Qt.LeftButton, pos=QtCore.QPoint(*data["br"]))

    def check_ocr_result():
        assert tray.capture.ocr_text

    qtbot.waitUntil(check_ocr_result)
    capture = tray.capture

    # Text output is not 100% predictable across different machines:
    similarity = Levenshtein.ratio(capture.ocr_text, data["transformed"])

    assert capture.ocr_applied_magic == data["ocr_applied_magic"], capture
    assert similarity >= 0.98, f"{capture.ocr_text=}"
