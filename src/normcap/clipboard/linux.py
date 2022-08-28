import logging
import os
import shutil
import subprocess

from normcap.clipboard import qt

logger = logging.getLogger(__name__)


def wl_copy(text):
    """Use wl-clipboard package to copy text to system clipboard."""
    subprocess.run(
        ["wl-copy"],
        shell=False,
        input=text,
        encoding="utf-8",
        check=True,
        timeout=30,
    )


def on_wayland():
    WAYLAND_DISPLAY = os.environ.get("WAYLAND_DISPLAY", "")
    XDG_SESSION_TYPE = os.environ.get("XDG_SESSION_TYPE", "")
    return "wayland" in WAYLAND_DISPLAY.lower() or "wayland" in XDG_SESSION_TYPE.lower()


def get_copy():

    if on_wayland():
        if shutil.which("wl-copy") is not None:
            logger.debug("Use wl-clipboard to copy to clipboard.")
            return wl_copy

        logger.warning(
            "Your display manager uses Wayland. Please install the system "
            "package 'wl-clipboard' to ensure that NormCap can copy its results to "
            "the clipboard correctly."
        )

    logger.debug("Use Qt to copy to clipboard.")
    return qt.copy
