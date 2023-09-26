import logging
import tempfile
import time
from pathlib import Path

from PySide6.QtGui import QImage

logger = logging.getLogger(__name__)


def save_image_in_temp_folder(image: QImage, postfix: str = "") -> None:
    """For debugging it can be useful to store the cropped image."""
    if logger.getEffectiveLevel() != logging.DEBUG:
        return

    temp_dir = Path(tempfile.gettempdir()) / "normcap"
    temp_dir.mkdir(exist_ok=True)

    now_str = time.strftime("%Y-%m-%d_%H-%M-%S", time.gmtime())
    file_name = f"{now_str}{postfix}.png"

    logger.debug("Save debug image as %s", temp_dir / file_name)
    image.save(str(temp_dir / file_name))
