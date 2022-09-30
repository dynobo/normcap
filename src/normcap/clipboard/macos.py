import logging
import shutil
import subprocess
from typing import Callable

from normcap.clipboard import qt

logger = logging.getLogger(__name__)


def pbcopy(text):
    subprocess.run(
        ["pbcopy", "w"],
        shell=False,
        input=text,
        encoding="utf-8",
        check=True,
        timeout=30,
    )


def get_copy_func() -> Callable:
    if shutil.which("pbcopy") is not None:
        logger.debug("Use pbcopy to copy to clipboard.")
        return pbcopy

    logger.debug("Use Qt to copy to clipboard.")
    return qt.copy
