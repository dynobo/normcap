import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from PySide6 import QtGui

from normcap.screenshot.post_processing import split_full_desktop_to_screens
from normcap.system import info

logger = logging.getLogger(__name__)

install_instructions = (
    "Install the package `spectacle` using your system's package manager."
)


def is_compatible() -> bool:
    return info.is_kde() and not info.is_flatpak()


def is_installed() -> bool:
    if not (spectacle_bin := shutil.which("spectacle")):
        return False

    logger.debug("%s dependencies are installed (%s)", __name__, spectacle_bin)
    return True


def capture() -> list[QtGui.QImage]:
    """Capture screenshot with the spectacle app.

    It is usually installed with KDE and should work even on wayland.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = Path(temp_dir) / "normcap_spectacle.png"
        subprocess.run(  # noqa: S603
            [  # noqa: S607
                "spectacle",
                "--fullscreen",
                "--background",
                "--nonotify",
                f"--output={image_path.resolve()}",
            ],
            shell=False,
            check=True,
            timeout=3,
            text=True,
            capture_output=True,
        )
        full_image = QtGui.QImage(image_path)

    return split_full_desktop_to_screens(full_image)
