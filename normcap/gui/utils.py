import datetime
import io
import logging
import tempfile
from pathlib import Path

from PIL import Image
from PySide6 import QtCore, QtGui

logger = logging.getLogger(__name__)


def _qimage_to_pil_image(image: QtGui.QImage) -> Image.Image:
    """Cast QImage to pillow Image type."""
    ba = QtCore.QByteArray()
    buffer = QtCore.QBuffer(ba)
    buffer.open(QtCore.QIODevice.ReadWrite)
    image.save(buffer, "PNG")  # type:ignore
    return Image.open(io.BytesIO(buffer.data()))


def _save_image_in_tempfolder(
    image: Image.Image, postfix: str = "", log_level: int = logging.DEBUG
) -> None:
    """For debugging it can be useful to store the cropped image."""
    if logger.getEffectiveLevel() == log_level:
        file_dir = Path(tempfile.gettempdir()) / "normcap"
        file_dir.mkdir(exist_ok=True)
        now = datetime.datetime.now()
        file_name = f"{now:%Y-%m-%d_%H-%M-%S_%f}{postfix}.png"
        logger.debug("Save debug image as %s", file_dir / file_name)
        image.save(str(file_dir / file_name))
