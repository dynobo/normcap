import logging
import tempfile
import time
from collections.abc import Callable
from functools import wraps
from pathlib import Path

from PySide6 import QtCore, QtGui

from normcap.system.models import Rect

logger = logging.getLogger(__name__)


def single_instance_slot(func: Callable) -> Callable:
    mutex = QtCore.QMutex()
    running = {"flag": False}

    @wraps(func)
    def wrapper(*args: tuple, **kwargs: dict) -> None:
        locker = QtCore.QMutexLocker(mutex)
        if running["flag"]:
            logger.debug("Skip %s() as already running.", {func.__name__})
            return
        running["flag"] = True
        locker.unlock()

        try:
            func(*args, **kwargs)
        finally:
            locker.relock()
            running["flag"] = False
            locker.unlock()
        return

    return wrapper


def crop_image(image: QtGui.QImage, rect: Rect) -> QtGui.QImage:
    """Crop image to selected region."""
    logger.info("Crop image to region %s", rect.coords)

    image = image.copy(QtCore.QRect(*rect.geometry))

    save_image_in_temp_folder(image, postfix="_cropped")
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
