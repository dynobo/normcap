import logging
import shutil
import subprocess
from typing import Callable

from normcap.clipboard import qt

logger = logging.getLogger(__name__)


def pbcopy(text: str) -> None:
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
        logger.debug("Select clipboard method pbcopy")
        return pbcopy

    logger.debug("Select clipboard method QT")
    return qt.copy
