import functools
import logging
import os
import re
import shutil
import subprocess
import sys

logger = logging.getLogger(__name__)


def has_wlroots_compositor() -> bool:
    """Check if wlroots compositor is running, as grim only supports wlroots.

    Certainly not wlroots based are: KDE, GNOME and Unity.
    Others are likely wlroots based.
    """
    if sys.platform != "linux":
        return False

    kde_full_session = os.environ.get("KDE_FULL_SESSION", "").lower()
    xdg_current_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    desktop_session = os.environ.get("DESKTOP_SESSION", "").lower()
    gnome_desktop_session_id = os.environ.get("GNOME_DESKTOP_SESSION_ID", "")
    if gnome_desktop_session_id == "this-is-deprecated":
        gnome_desktop_session_id = ""

    if (
        gnome_desktop_session_id
        or "gnome" in xdg_current_desktop
        or kde_full_session
        or "kde-plasma" in desktop_session
        or "unity" in xdg_current_desktop
    ):
        return False

    return True


def has_wayland_display_manager() -> bool:
    """Identify relevant display managers (Linux)."""
    if sys.platform != "linux":
        return False

    xdg_session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    has_wayland_display_env = bool(os.environ.get("WAYLAND_DISPLAY", ""))
    return "wayland" in xdg_session_type or has_wayland_display_env


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
