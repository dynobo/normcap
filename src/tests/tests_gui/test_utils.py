import logging
import os
import sys
import tempfile
from pathlib import Path

import pytest
from normcap import clipboard
from normcap.gui import utils
from PySide6 import QtCore, QtGui


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

    utils.save_image_in_tempfolder(image, postfix="unittest")

    png_files = (Path(tempfile.gettempdir()) / "normcap").glob("*.png")
    png_files = sorted(png_files, key=os.path.getmtime, reverse=True)
    assert "unittest" in str(list(png_files)[0])


def test_get_icon_custom():
    icon = utils.get_icon("normcap.png")
    assert icon.name() == ""
    assert len(icon.availableSizes()) == 1


@pytest.mark.skip_on_gh
def test_get_icon_sytem():
    icon = utils.get_icon("normcap.png", "edit-undo")
    icon_gnome43 = utils.get_icon("normcap.png", "edit-undo-symbolic")
    assert icon.name() == "edit-undo" or icon_gnome43.name() == "edit-undo-symbolic"
    assert len(icon.availableSizes()) >= 1


def test_get_icon_sytem_use_fallback():
    icon = utils.get_icon("normcap.png", "not-existing-icon")
    assert icon.name() == ""
    assert len(icon.availableSizes()) == 1


def test_set_cursor():
    # I do not know how to read cursor shape. Therefor I just test that
    # no exceptions are thrown.
    utils.set_cursor()
    utils.set_cursor(QtCore.Qt.CrossCursor)
