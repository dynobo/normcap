import logging
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from PySide6 import QtCore, QtGui

from normcap import clipboard
from normcap.gui import utils


def test_copy_to_clipboard():
    if sys.platform.lower() == "linux":
        return

    text = "To be copied to system clipboard"
    _copy_to_clipboard = clipboard.get_copy_func()
    _copy_to_clipboard(text)

    read_from_clipboard = QtGui.QGuiApplication.clipboard()
    text_from_clipboard = read_from_clipboard.text()

    assert text_from_clipboard == text


def test_save_image_in_tempfolder():
    logger = logging.getLogger(__name__).root
    logger.setLevel("DEBUG")

    image = QtGui.QImage(20, 20, QtGui.QImage.Format.Format_RGB32)

    test_id = f"_unittest_{datetime.now():%H-%M-%S.%f}"
    utils.save_image_in_tempfolder(image, postfix=test_id)

    png_files = (Path(tempfile.gettempdir()) / "normcap").glob(f"*{test_id}.png")
    assert len(list(png_files)) == 1


def test_set_cursor():
    # I do not know how to read cursor shape. Therefor I just test that
    # no exceptions are thrown.
    utils.set_cursor()
    utils.set_cursor(QtCore.Qt.CrossCursor)
