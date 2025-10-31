import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from PySide6 import QtGui

from normcap.screenshot.post_processing import split_full_desktop_to_screens
from normcap.system import info

logger = logging.getLogger(__name__)

install_instructions = "Install the package `grim` using your system's package manager."


def is_compatible() -> bool:
    return info.has_wlroots_compositor() and not info.is_flatpak()


def is_installed() -> bool:
    if not (grim_bin := shutil.which("grim")):
        return False

    logger.debug("%s dependencies are installed (%s)", __name__, grim_bin)
    return True


def capture() -> list[QtGui.QImage]:
    """Capture screenshot with the grim CLI tool for wayland.

    Is supported by some wayland compositors, e.g. hyprland. Won't work on e.g.
    standard Gnome.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = Path(temp_dir) / "normcap_grim_screenshot.png"
        subprocess.run(  # noqa: S603
            ["grim", str(image_path.resolve())],  # noqa: S607
            shell=False,
            check=True,
            timeout=3,
            text=True,
            capture_output=True,
        )
        full_image = QtGui.QImage(image_path)

    return split_full_desktop_to_screens(full_image)
