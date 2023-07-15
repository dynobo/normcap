import logging
import re
import tempfile
from pathlib import Path
from time import time

from PySide6 import QtGui

from normcap.gui import utils


def test_save_image_in_tempfolder():
    # GIVEN the logger is set to level DEBUG
    #   and a QImage
    logger = logging.getLogger(__name__).root
    logger.setLevel("DEBUG")

    image = QtGui.QImage(20, 20, QtGui.QImage.Format.Format_RGB32)

    # WHEN the image is saved to the tempfolder
    test_id = f"_unittest_{time()}"
    utils.save_image_in_temp_folder(image, postfix=test_id)

    # THEN exactly one file should be created in <tempdir>/normcap folder
    #   and it should be a png, prefixed with current datetime
    png_files = list((Path(tempfile.gettempdir()) / "normcap").glob(f"*{test_id}*"))
    assert len(png_files) == 1
    assert png_files[0].suffix == ".png"
    assert re.fullmatch(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_.*", png_files[0].stem)
