import logging
import os
import shutil
import subprocess
from typing import Callable

from normcap.clipboard import qt

logger = logging.getLogger(__name__)


def _wl_copy(text: str) -> None:
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
    wayland_display = os.environ.get("WAYLAND_DISPLAY", "")
    xdg_session_type = os.environ.get("XDG_SESSION_TYPE", "")
    return "wayland" in wayland_display.lower() or "wayland" in xdg_session_type.lower()


def get_copy_func() -> Callable:

    if _is_wayland_display_manager():
        if shutil.which("wl-copy") is not None:
            logger.debug("Select clipboard method wl-copy")
            return _wl_copy

        logger.warning(
            "Your display manager uses Wayland. Please install the system "
            "package 'wl-clipboard' to ensure that NormCap can copy its results to "
            "the clipboard correctly."
        )

    logger.debug("Select clipboard method QT")
    return qt.copy
