import logging
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


install_instructions = (
    "Please install the package 'xsel' " "with your system's package manager."
)


def copy(text: str) -> None:
    """Use xsel package to copy text to system clipboard."""
    subprocess.run(
        args=["xsel", "--clipboard", "--input"],
        shell=False,
        input=text,
        encoding="utf-8",
        check=True,
        # It seems like wl-copy works more reliable when output is piped to
        # somewhere. This is e.g. the case when NormCap got started via a shortcut
        # on KDE (#422).
        stdout=Path("/dev/null").open("w"),  # noqa: SIM115
        timeout=30,
    )


def is_compatible() -> bool:
    if sys.platform != "linux":
        logger.debug("%s is not compatible on non-Linux systems", __name__)
        return False

    logger.debug("%s is compatible", __name__)
    return True


def is_installed() -> bool:
    if not (xclip_bin := shutil.which("xsel")):
        logger.debug("%s is not installed: xsel was not found", __name__)
        return False

    logger.debug("%s dependencies are installed (%s)", __name__, xclip_bin)
    return True
