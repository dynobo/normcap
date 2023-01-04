import logging
import sys
import tempfile
from datetime import datetime
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

    test_id = f"_unittest_{datetime.now():%H-%M-%S.%f}"
    utils.save_image_in_tempfolder(image, postfix=test_id)

    png_files = (Path(tempfile.gettempdir()) / "normcap").glob(f"*{test_id}.png")
    assert len(list(png_files)) == 1


@pytest.mark.parametrize(
    "icon_name",
    (
        "normcap.png",  # use extension to override system icon
        "tool-magic-symbolic.png",  # use extension to override system icon
        "normcap-raw",
        "normcap-parse",
        "normcap-settings",
    ),
)
def test_get_icon_custom(qtbot, icon_name):
    icon = utils.get_icon(icon_name)
    assert icon.name() == ""
    assert not icon.isNull()


def test_get_icon_default(qtbot):
    icon = utils.get_icon("SP_DialogApplyButton")
    assert not icon.isNull()


@pytest.mark.skip_on_gh
def test_get_icon_system(qtbot):
    icon = utils.get_icon("edit")
    assert not icon.isNull()


def test_get_icon_raise_on_not_existing(qtbot):
    icon_name = "not-existing-icon"
    with pytest.raises(ValueError, match=icon_name):
        _ = utils.get_icon("not-existing-icon")


def test_set_cursor():
    # I do not know how to read cursor shape. Therefor I just test that
    # no exceptions are thrown.
    utils.set_cursor()
    utils.set_cursor(QtCore.Qt.CrossCursor)
