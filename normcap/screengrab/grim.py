import logging
import subprocess
import tempfile
from pathlib import Path

from PySide6 import QtGui

from normcap.screengrab.utils import split_full_desktop_to_screens

logger = logging.getLogger(__name__)


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
