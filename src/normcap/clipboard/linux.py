import logging
import os
import shutil
import subprocess
from typing import Callable

from normcap.clipboard import qt

logger = logging.getLogger(__name__)


def _wl_copy(text):
    """Use wl-clipboard package to copy text to system clipboard."""
    subprocess.run(
        ["wl-copy"],
        shell=False,
        input=text,
        encoding="utf-8",
        check=True,
        timeout=30,
    )


def _is_wayland_display_manager() -> bool:
    WAYLAND_DISPLAY = os.environ.get("WAYLAND_DISPLAY", "")
    XDG_SESSION_TYPE = os.environ.get("XDG_SESSION_TYPE", "")
    return "wayland" in WAYLAND_DISPLAY.lower() or "wayland" in XDG_SESSION_TYPE.lower()


def get_copy_func() -> Callable:

    if _is_wayland_display_manager():
        if shutil.which("wl-copy") is not None:
            logger.debug("Use wl-clipboard to copy to clipboard.")
            return _wl_copy

        logger.warning(
            "Your display manager uses Wayland. Please install the system "
            "package 'wl-clipboard' to ensure that NormCap can copy its results to "
            "the clipboard correctly."
        )

    logger.debug("Use Qt to copy to clipboard.")
    return qt.copy
