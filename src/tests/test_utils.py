import logging
import os
import tempfile
from importlib import resources
from pathlib import Path

import pytest
from PySide6 import QtCore, QtGui

from normcap.gui import utils

# Specific settings for pytest
# pylint: disable=redefined-outer-name,protected-access,unused-argument


def test_init_tessdata_copies_files(tmp_path, monkeypatch):
    # Create placeholder for traineddata files, if they don't exist
    resource_path = Path(resources.files("normcap.resources"))
    traineddata_files = list((resource_path / "tessdata").glob("*.traineddata"))
    if not traineddata_files:
        (resource_path / "tessdata" / "placeholder_1.traineddata").touch()
        (resource_path / "tessdata" / "placeholder_2.traineddata").touch()

    try:
        monkeypatch.setattr(utils.system_info, "config_directory", lambda: tmp_path)
        tessdata_path = tmp_path / "tessdata"

        traineddatas = list(tessdata_path.glob("*.traineddata"))
        txts = list(tessdata_path.glob("*.txt"))
        assert not traineddatas
        assert not txts

        for _ in range(3):
            utils.copy_tessdata_files_to_config_dir()

            traineddatas = list(tessdata_path.glob("*.traineddata"))
            txts = list(tessdata_path.glob("*.txt"))
            assert traineddatas
            assert len(txts) == 1
    finally:
        # Make sure to delete possible placeholder files
        for f in (resource_path / "tessdata").glob("placeholder_?.traineddata"):
            f.unlink()


@pytest.mark.skip_on_gh_linux
def test_copy_to_clipboard():
    text = "To be copied to system clipboard"
    _copy_to_clipboard = utils.copy_to_clipboard()
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


def test_get_icon(qtbot):
    # Custom icon
    icon = utils.get_icon("normcap.png")
    assert len(icon.availableSizes()) == 1

    # System icon
    icon = utils.get_icon("not-relevant", "edit-undo")
    assert len(icon.availableSizes()) >= 3


def test_set_cursor(qtbot):
    # I do not know how to read cursor shape. Therefor I just test that
    # no exceptions are thrown.
    utils.set_cursor()
    utils.set_cursor(QtCore.Qt.CrossCursor)


def test_qt_log_wrapper(qtlog, caplog):
    logger = logging.getLogger(__name__).root
    logger.setLevel("DEBUG")
    QtCore.qDebug("should_show_in_qtlog_only")
    QtCore.qInstallMessageHandler(utils.qt_log_wrapper)
    QtCore.qDebug("should_show_in_logger_only")

    qt_log_entries = [m.message.strip() for m in qtlog.records]
    assert len(qt_log_entries) == 1
    assert qt_log_entries[0] == "should_show_in_qtlog_only"

    assert "should_show_in_qtlog_only" not in caplog.text
    assert "should_show_in_logger_only" in caplog.text
    assert "[QT]" in caplog.text
    assert "debug" in caplog.text


def test_qt_log_wrapper_no_platform_as_error(caplog):
    logger = logging.getLogger(__name__).root
    logger.setLevel("DEBUG")
    QtCore.qInstallMessageHandler(utils.qt_log_wrapper)

    QtCore.qDebug("could not load the qt platform")

    assert "could not load the qt platform" in caplog.text
    assert "[qt]" in caplog.text.lower()
    assert "error" in caplog.text.lower()


def test_qt_log_wrapper_xcb_as_error(caplog):
    logger = logging.getLogger(__name__).root
    logger.setLevel("DEBUG")
    QtCore.qInstallMessageHandler(utils.qt_log_wrapper)

    QtCore.qDebug("xcb it was found")

    assert "[qt]" in caplog.text.lower()
    assert "xcb it was found" in caplog.text.lower()
    assert "try solving the problem" in caplog.text.lower()
    assert "error" in caplog.text.lower()
