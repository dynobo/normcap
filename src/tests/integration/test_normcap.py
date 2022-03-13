import logging
from pathlib import Path

import Levenshtein
import pytest
from PySide6 import QtCore, QtGui, QtWidgets

import normcap
from normcap.args import create_argparser
from normcap.gui.window import Window

from .testcases.data import TESTCASES

logger = logging.getLogger(__name__)

# Specific settings for pytest
# pylint: disable=redefined-outer-name,protected-access,unused-argument


@pytest.mark.parametrize(
    "data",
    TESTCASES,
)
def test_app(monkeypatch, qtbot, xvfb, data):
    """Tests complete OCR workflow."""
    logger.setLevel("DEBUG")
    args = create_argparser().parse_args([f"--language={data['language']}"])
    test_file = Path(__file__).parent / "testcases" / data["image"]
    test_image = QtGui.QImage(test_file.absolute())

    app = QtWidgets.QApplication.instance()
    screen_rect = app.primaryScreen().size()

    if screen_rect.width() != 1920 or screen_rect.height() != 1080:
        pytest.xfail("Skipped due to wrong screen resolution.")

    # Avoid flickering on wayland during test
    monkeypatch.setattr(
        normcap.gui.window.Window,
        "_position_windows_on_wayland",
        lambda _: True,
    )
    monkeypatch.setattr(
        normcap.gui.window,
        "grab_screens",
        lambda: [test_image],
    )

    window = Window(vars(args))
    qtbot.addWidget(window)
    window.show()

    with qtbot.waitSignal(window.tray.com.on_copied_to_clipboard):
        qtbot.mousePress(window, QtCore.Qt.LeftButton, pos=QtCore.QPoint(*data["tl"]))
        qtbot.mouseMove(window, pos=QtCore.QPoint(*data["br"]))
        qtbot.mouseRelease(window, QtCore.Qt.LeftButton, pos=QtCore.QPoint(*data["br"]))

    capture = window.tray.capture
    print(capture.rect)
    print(data["br"])

    # Text output is not 100% predictable across different machines:
    similarity = Levenshtein.ratio(capture.ocr_text, data["transformed"])

    assert (
        capture.ocr_applied_magic == data["ocr_applied_magic"]
    ), f"{capture.ocr_text=}"
    assert similarity >= 0.98, f"{capture.ocr_text=}"
