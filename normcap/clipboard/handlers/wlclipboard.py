import logging
import shutil
import subprocess
from pathlib import Path

from normcap.system import info

logger = logging.getLogger(__name__)


install_instructions = (
    "Please install the package 'wl-clipboard' with your system's package manager."
)


def copy(text: str) -> None:
    """Use wl-clipboard package to copy text to system clipboard."""
    if gnome_version := info.get_gnome_version():
        gnome_major = int(gnome_version.split(".")[0])
        last_working_gnome_version = 44
        if gnome_major > last_working_gnome_version:
            logger.warning(
                "%s is not working well with Gnome %s. Try installing xclip or xsel!",
                __name__,
                gnome_version,
            )

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
    if not info.has_wayland_display_manager():
        return False

    if info.has_awesome_wm():
        return False

    if info.is_flatpak():
        return True

    return True


def is_installed() -> bool:
    # ONHOLD: Wait for feedback on new qt_wayland handler, then remove wlclipboard
    #  from FlatPak
    if not (wl_copy_bin := shutil.which("wl-copy")):
        return False

    logger.debug("%s dependencies are installed (%s)", __name__, wl_copy_bin)
    return True
