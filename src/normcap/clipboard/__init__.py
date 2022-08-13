import logging
import os
import shutil

from normcap.clipboard import qt, wl_clipboard

logger = logging.getLogger(__name__)


def get_copy_func():
    WAYLAND_DISPLAY = os.environ.get("WAYLAND_DISPLAY", "")
    XDG_SESSION_TYPE = os.environ.get("XDG_SESSION_TYPE", "")
    on_wayland = (
        "wayland" in WAYLAND_DISPLAY.lower() or "wayland" in XDG_SESSION_TYPE.lower()
    )

    if on_wayland:
        has_wl_clipboard = shutil.which("wl-copy") is not None if on_wayland else False

        if not has_wl_clipboard:
            logger.warning(
                "Your display manager uses Wayland but. Please install the system "
                "package 'wl-clipboard' to ensure that NormCap can copy its results to "
                "the clipboard correctly."
            )
            logger.debug("Use Qt to copy to clipboard.")
            return qt.copy

        logger.debug("Use wl-clipboard to copy to clipboard.")
        return wl_clipboard.copy

    logger.debug("Use Qt to copy to clipboard.")
    return qt.copy


def copy(text):
    get_copy_func()(text)
