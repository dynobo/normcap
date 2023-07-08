import logging
import tempfile
from datetime import datetime
from pathlib import Path

from PySide6 import QtGui

from normcap.gui import utils


def testsave_image_in_temp_folder():
    logger = logging.getLogger(__name__).root
    logger.setLevel("DEBUG")

    image = QtGui.QImage(20, 20, QtGui.QImage.Format.Format_RGB32)

    test_id = f"_unittest_{datetime.now():%H-%M-%S.%f}"
    utils.save_image_in_temp_folder(image, postfix=test_id)

    png_files = (Path(tempfile.gettempdir()) / "normcap").glob(f"*{test_id}.png")
    assert len(list(png_files)) == 1
