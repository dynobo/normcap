import re
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from PySide6 import QtGui

from normcap.gui import utils


def test_save_image_in_tempfolder():
    # GIVEN the logger is set to level DEBUG
    #   and a QImage
    utils.logger.setLevel("DEBUG")

    image = QtGui.QImage(20, 20, QtGui.QImage.Format.Format_RGB32)

    # WHEN the image is saved to the tempfolder
    test_id = f"_unittest_{uuid4()}"
    utils.save_image_in_temp_folder(image, postfix=test_id)

    # THEN exactly one file should be created in <tempdir>/normcap folder
    #   and it should be a png, prefixed with current datetime
    png_files = list((Path(tempfile.gettempdir()) / "normcap").glob(f"*{test_id}*"))
    assert len(png_files) == 1
    assert png_files[0].suffix == ".png"
    assert re.fullmatch(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_.*", png_files[0].stem)


@pytest.mark.parametrize("log_level", ["WARNING", "ERROR"])
def test_save_image_in_tempfolder_skip_if_loglevel_not_debug(log_level):
    # GIVEN the logger is set to level other than DEBUG
    #   and a QImage
    utils.logger.setLevel(log_level)
    image = QtGui.QImage(20, 20, QtGui.QImage.Format.Format_RGB32)

    # WHEN the image is saved to the tempfolder
    test_id = f"_unittest_{uuid4()}"
    utils.save_image_in_temp_folder(image, postfix=test_id)

    # THEN the file should _not_ be created in <tempdir>/normcap folder
    png_files = list((Path(tempfile.gettempdir()) / "normcap").glob(f"*{test_id}*"))
    assert len(png_files) == 0
