import datetime
import logging
import tempfile
from pathlib import Path

from PySide6.QtGui import QImage

logger = logging.getLogger(__name__)


def _save_image_in_tempfolder(
    image: QImage, postfix: str = "", log_level: int = logging.DEBUG
) -> None:
    """For debugging it can be useful to store the cropped image."""
    if logger.getEffectiveLevel() == log_level:
        file_dir = Path(tempfile.gettempdir()) / "normcap"
        file_dir.mkdir(exist_ok=True)
        now = datetime.datetime.now()
        file_name = f"{now:%Y-%m-%d_%H-%M-%S_%f}{postfix}.png"
        logger.debug("Save debug image as %s", file_dir / file_name)
        image.save(str(file_dir / file_name))
