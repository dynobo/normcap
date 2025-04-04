import logging
import tempfile
import time
from pathlib import Path

from PySide6 import QtCore, QtGui

from normcap.gui.models import Rect

logger = logging.getLogger(__name__)


def crop_image(image: QtGui.QImage, rect: Rect) -> QtGui.QImage:
    """Crop image to selected region."""
    logger.info("Crop image to region %s", rect.coords)

    image = image.copy(QtCore.QRect(*rect.geometry))

    save_image_in_temp_folder(image, postfix="_croped")
    return image


def save_image_in_temp_folder(image: QtGui.QImage, postfix: str = "") -> None:
    """For debugging it can be useful to store the cropped image."""
    if logger.getEffectiveLevel() != logging.DEBUG:
        return

    temp_dir = Path(tempfile.gettempdir()) / "normcap"
    temp_dir.mkdir(exist_ok=True)

    now_str = time.strftime("%Y-%m-%d_%H-%M-%S", time.gmtime())
    file_name = f"{now_str}{postfix}.png"

    logger.debug("Save debug image as %s", temp_dir / file_name)
    image.save(str(temp_dir / file_name))
