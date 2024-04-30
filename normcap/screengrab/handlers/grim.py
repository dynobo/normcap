import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PySide6 import QtGui

from normcap.screengrab import system_info
from normcap.screengrab.post_processing import split_full_desktop_to_screens

logger = logging.getLogger(__name__)

install_instructions = "Install the package `grim` using your system's package manager."


def is_compatible() -> bool:
    return (
        sys.platform == "linux"
        and system_info.has_wayland_display_manager()
        and system_info.has_wlroots_compositor()
    )


def is_installed() -> bool:
    return bool(shutil.which("grim"))


def capture() -> list[QtGui.QImage]:
    """Capture screenshot with the grim CLI tool for wayland.

    Is supported by some wayland compositors, e.g. hyprland. Won't work on e.g.
    standard Gnome.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = Path(temp_dir) / "normcap_grim_screenshot.png"
        subprocess.run(
            ["grim", str(image_path.resolve())],  # noqa: S607
            shell=False,  # noqa: S603
            check=True,
            timeout=3,
            text=True,
            capture_output=True,
        )
        full_image = QtGui.QImage(image_path)

    return split_full_desktop_to_screens(full_image)
