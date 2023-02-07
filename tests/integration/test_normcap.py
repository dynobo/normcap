import logging
import sys
from pathlib import Path

import Levenshtein
import pytest
from PySide6 import QtCore, QtGui

from normcap import app
from normcap.gui.tray import SystemTray, screengrab

from .testcases.data import TESTCASES

logger = logging.getLogger(__name__)


def _check_ocr_result(normcap_tray):
    def __check_ocr_result():
        assert normcap_tray.capture.ocr_text

    return __check_ocr_result


def _load_test_image(image):
    def __load_test_image():
        return [image]

    return __load_test_image


@pytest.mark.gui
@pytest.mark.parametrize("data", TESTCASES[:1])
def test_app(monkeypatch, qapp, qtbot, data):
    """Tests complete OCR workflow."""
    screen_rect = qapp.primaryScreen().size()

    image = QtGui.QImage(Path(__file__).parent / "testcases" / data["image"])
    top_left = QtCore.QPoint(*data["tl"])
    bottom_right = QtCore.QPoint(*data["br"])

    # Scale test data, if necessary
    if screen_rect.width() != image.width() or screen_rect.height() != image.height():
        x_factor = image.width() / screen_rect.width()
        y_factor = image.height() / screen_rect.height()
        factor = max(x_factor, y_factor)

        top_left /= factor
        bottom_right /= factor
        image = image.scaled(
            image.width() // factor,
            image.height() // factor,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        image_full = QtGui.QImage(screen_rect, image.format())
        with QtGui.QPainter(image_full) as p:
            p.drawImage(0, 0, image)
        image = image_full

    with monkeypatch.context() as m:
        m.setattr(screengrab, "get_capture_func", lambda: _load_test_image(image))
        m.setattr(
            sys,
            "argv",
            [
                sys.argv[0],
                "--language=eng",
                "--mode=parse",
                "--tray=True",
                "--verbosity=debug",
                "--update=False",
            ],
        )
        args = app._get_args()
        app._prepare_logging(args)
        app._prepare_envs()

        tray = SystemTray(None, vars(args))
        tray.setVisible(True)

        window = tray.windows[0]
        qtbot.mousePress(window, QtCore.Qt.LeftButton, pos=top_left)
        qtbot.mouseMove(window, pos=bottom_right)
        qtbot.mouseRelease(window, QtCore.Qt.LeftButton, pos=bottom_right)

        qtbot.waitUntil(_check_ocr_result(tray))
        capture = tray.capture

        # Text output is not 100% predictable across different machines:
        similarity = Levenshtein.ratio(capture.ocr_text, data["transformed"])

    assert capture.ocr_applied_magic == data["ocr_applied_magic"], capture.ocr_text
    assert similarity >= 0.98, f"{capture.ocr_text=}"
