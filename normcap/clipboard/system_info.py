import functools
import logging
import os
import re
import shutil
import subprocess
import sys

logger = logging.getLogger(__name__)


def os_has_wayland_display_manager() -> bool:
    if sys.platform != "linux":
        return False

    xdg_session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    has_wayland_display_env = bool(os.environ.get("WAYLAND_DISPLAY", ""))
    return "wayland" in xdg_session_type or has_wayland_display_env


def os_has_awesome_wm() -> bool:
    if sys.platform != "linux":
        return False

    return "awesome" in os.environ.get("XDG_CURRENT_DESKTOP", "").lower()


def is_flatpak_package() -> bool:
    return os.getenv("FLATPAK_ID") is not None


@functools.cache
def get_gnome_version() -> str:
    """Detect Gnome version of current session.

    Returns:
        Version string or empty string if not detected.
    """
    if sys.platform != "linux":
        return ""

    if (
        not os.environ.get("GNOME_DESKTOP_SESSION_ID", "")
        and "gnome" not in os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    ):
        return ""

    if not shutil.which("gnome-shell"):
        return ""

    try:
        output = subprocess.check_output(
            ["gnome-shell", "--version"],  # noqa: S607
            shell=False,  # noqa: S603
            text=True,
        )
        if result := re.search(r"\s+([\d\.]+)", output.strip()):
            gnome_version = result.groups()[0]
    except Exception as e:
        logger.warning("Exception when trying to get gnome version from cli %s", e)
        return ""
    else:
        return gnome_version
