import logging
import time
from pathlib import Path

import Levenshtein
import pytest
from PySide6 import QtCore, QtGui

import normcap
from normcap.gui.tray import SystemTray
from normcap.utils import create_argparser

from .testcases.data import TESTCASES

logger = logging.getLogger(__name__)


def _check_ocr_result(normcap_tray):
    def __check_ocr_result():
        assert normcap_tray.capture.ocr_text

    return __check_ocr_result


def _load_test_image(image_path):
    def __load_test_image():
        return [QtGui.QImage(image_path.resolve())]

    return __load_test_image


@pytest.mark.parametrize("data", TESTCASES)
def test_app(monkeypatch, qapp, qtbot, data):
    """Tests complete OCR workflow."""
    screen_rect = qapp.primaryScreen().size()
    if screen_rect.width() != 1920 or screen_rect.height() != 1080:
        pytest.xfail("Skipped due to wrong screen resolution.")

    image = Path(__file__).parent / "testcases" / data["image"]
    monkeypatch.setattr(normcap.gui.tray, "grab_screens", _load_test_image(image))
    args = create_argparser().parse_args(
        ["--language=eng", "--mode=parse", "--tray=True"]
    )
    tray = SystemTray(None, vars(args))
    tray.show()

    window = tray.windows[0]
    qtbot.mousePress(window, QtCore.Qt.LeftButton, pos=QtCore.QPoint(*data["tl"]))
    qtbot.mouseMove(window, pos=QtCore.QPoint(*data["br"]))
    qtbot.mouseRelease(window, QtCore.Qt.LeftButton, pos=QtCore.QPoint(*data["br"]))

    qtbot.waitUntil(_check_ocr_result(tray))
    capture = tray.capture

    # Text output is not 100% predictable across different machines:
    similarity = Levenshtein.ratio(capture.ocr_text, data["transformed"])

    assert capture.ocr_applied_magic == data["ocr_applied_magic"], capture.ocr_text
    assert similarity >= 0.98, f"{capture.ocr_text=}"

    tray.com.on_quit.emit()
    time.sleep(0.5)
