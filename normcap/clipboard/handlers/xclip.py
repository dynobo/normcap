import logging
import shutil
import subprocess
import sys
from pathlib import Path

from normcap.clipboard import system_info

logger = logging.getLogger(__name__)


install_instructions = (
    "Please install the package 'xclip' with your system's package manager."
)


def copy(text: str) -> None:
    """Use xclip package to copy text to system clipboard."""
    subprocess.run(
        args=["xclip", "-selection", "clipboard", "-in"],
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
    if sys.platform != "linux" and "bsd" not in sys.platform:
        return False

    return not system_info.is_flatpak()


def is_installed() -> bool:
    if not (xclip_bin := shutil.which("xclip")):
        return False

    logger.debug("%s dependencies are installed (%s)", __name__, xclip_bin)
    return True
