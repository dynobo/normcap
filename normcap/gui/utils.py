import logging
import tempfile
import time
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
        now = time.time()
        now_str = time.strftime("%Y-%m-%d_%H-%M-%S", time.gmtime(now))
        now_str += f"{now % 1}"[:-3]
        file_name = f"{now}{postfix}.png"
        logger.debug("Save debug image as %s", file_dir / file_name)
        image.save(str(file_dir / file_name))
