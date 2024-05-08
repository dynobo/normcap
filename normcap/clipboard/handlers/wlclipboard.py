import logging
import shutil
import subprocess
from pathlib import Path

from normcap.clipboard import system_info

logger = logging.getLogger(__name__)


install_instructions = (
    "Please install the package 'wl-clipboard' with your system's package manager."
)


def copy(text: str) -> None:
    """Use wl-clipboard package to copy text to system clipboard."""
    subprocess.run(
        args=["wl-copy"],
        shell=False,
        input=text,
        encoding="utf-8",
        check=True,
        # It seems like wl-copy works more reliable when output is piped to
        # somewhere. This is e.g. the case when NormCap got started via a shortcut
        # on KDE (#422).
        stdout=Path("/dev/null").open("w"),  # noqa: SIM115
        timeout=5,
    )


def is_compatible() -> bool:
    if not system_info.os_has_wayland_display_manager():
        logger.debug(
            "%s is not compatible on non-Linux systems and on Linux w/o Wayland",
            __name__,
        )
        return False

    if system_info.os_has_awesome_wm():
        logger.debug("%s is not compatible with Awesome WM", __name__)
        return False

    if gnome_version := system_info.get_gnome_version():
        gnome_major = int(gnome_version.split(".")[0])
        last_working_gnome_version = 44
        if gnome_major > last_working_gnome_version:
            logger.debug("%s is not compatible with Gnome %s", __name__, gnome_version)
            return False

    logger.debug("%s is compatible", __name__)
    return True


def is_installed() -> bool:
    if not (wl_copy_bin := shutil.which("wl-copy")):
        logger.debug("%s is not installed: wl-copy was not found", __name__)
        return False

    logger.debug("%s dependencies are installed (%s)", __name__, wl_copy_bin)
    return True
