import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from PySide6 import QtGui

from normcap.screenshot import system_info
from normcap.screenshot.post_processing import split_full_desktop_to_screens

logger = logging.getLogger(__name__)

install_instructions = (
    "Install the package `gnome-screenshot` using your system's package manager."
)

# ONHOLD: Remove gnome-screenshot handler on EOL of Gnome 48
# It got removed from gnome core apps and therefore lost trusted access to screenshot.
LAST_GNOME_VERSION_SUPPORTED = 48


def is_compatible() -> bool:
    if not system_info.is_gnome() or system_info.is_flatpak():
        return False

    if gnome_version := system_info.get_gnome_version():
        gnome_major = int(gnome_version.split(".")[0])
        return gnome_major <= LAST_GNOME_VERSION_SUPPORTED

    # Assume the best and try this handler
    return True


def is_installed() -> bool:
    if not (screenshot_bin := shutil.which("gnome-screenshot")):
        return False

    logger.debug("%s dependencies are installed (%s)", __name__, screenshot_bin)
    return True


def capture() -> list[QtGui.QImage]:
    """Capture screenshot with the gnome-screenshot app.

    It is usually installed with Gnome and should work even on wayland.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = Path(temp_dir) / "normcap_gnome_screenshot.png"
        result = subprocess.run(  # noqa: S603
            ["gnome-screenshot", f"--file={image_path.resolve()}"],  # noqa: S607
            shell=False,
            check=False,
            timeout=3,
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            logger.error(
                "Command '%s' failed: %s", " ".join(result.args), result.stderr
            )
            result.check_returncode()

        full_image = QtGui.QImage(image_path)

    return split_full_desktop_to_screens(full_image)
