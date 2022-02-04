import logging
from pathlib import Path

import pytest
import toml
from PySide6 import QtCore, QtGui

import normcap
from normcap.args import create_argparser
from normcap.gui.main_window import MainWindow

from .ocr_testcases import TESTCASES

logger = logging.getLogger(__name__)

# Specific settings for pytest
# pylint: disable=redefined-outer-name,protected-access,unused-argument


def test_version():
    with open("pyproject.toml", encoding="utf8") as toml_file:
        pyproject_toml = toml.load(toml_file)

    briefcase_version = pyproject_toml["tool"]["briefcase"]["version"]
    poetry_version = pyproject_toml["tool"]["poetry"]["version"]
    assert briefcase_version == poetry_version == normcap.__version__


@pytest.mark.parametrize(
    "data",
    TESTCASES,
)
def test_app(monkeypatch, qtbot, xvfb, data):
    """Tests complete OCR workflow."""
    logger.setLevel("DEBUG")
    args = create_argparser().parse_args([f"--language={data['language']}"])
    test_file = Path(__file__).parent / "testcase_images" / data["image"]
    monkeypatch.setattr(
        normcap.gui.main_window,
        "grab_screens",
        lambda: [QtGui.QImage(test_file.absolute())],
    )

    window = MainWindow(vars(args))
    window.show()
    qtbot.addWidget(window)

    with qtbot.waitSignal(window.main_window.com.on_copied_to_clipboard):
        qtbot.mousePress(window, QtCore.Qt.LeftButton, pos=QtCore.QPoint(*data["tl"]))
        qtbot.mouseMove(window, pos=QtCore.QPoint(*data["br"]))
        qtbot.mouseRelease(window, QtCore.Qt.LeftButton, pos=QtCore.QPoint(*data["br"]))

    assert window.main_window.capture.ocr_text == data["transformed"]
