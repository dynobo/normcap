import logging
import os
import shutil
import signal
from pathlib import Path

from normcap.system import info

logger = logging.getLogger(__name__)


def _set_environ_for_wayland() -> None:
    # QT has 32 as default cursor size on wayland, while it should be 24
    if "XCURSOR_SIZE" not in os.environ:
        logger.debug("Set XCURSOR_SIZE=24")
        os.environ["XCURSOR_SIZE"] = "24"

    # Select wayland extension for better rendering
    if "QT_QPA_PLATFORM" not in os.environ:
        logger.debug("Set QT_QPA_PLATFORM=wayland")
        os.environ["QT_QPA_PLATFORM"] = "wayland"


def _set_environ_for_appimage() -> None:
    # Append path to shipped binaries to PATH
    bin_path = str(Path(__file__).resolve().parents[2] / "bin")
    logger.debug("Append %s to AppImage internal PATH", bin_path)
    os.environ["PATH"] = (
        os.environ.get("PATH", "").rstrip(os.pathsep) + os.pathsep + bin_path
    )


def _set_environ_for_flatpak() -> None:
    """Set the environment variables for running the code within a FlatPak.

    This function deactivates the gtk-nocsd feature within a FlatPak, because it does
    not work in that context.

    Note: gtk-nocsd is used by certain desktop environments, such as Unity, to remove
          client-side decorations.

    See also: https://github.com/dynobo/normcap/issues/290#issuecomment-1289629427
    """
    ld_preload = os.environ.get("LD_PRELOAD", "")

    if "nocsd" in ld_preload.lower():
        logger.warning(
            "Found LD_PRELOAD='%s'. Setting to LD_PRELOAD='' to avoid issues.",
            ld_preload,
        )
        os.environ["LD_PRELOAD"] = ""


def copy_traineddata_files(target_dir: Path | None) -> None:
    """Copy Tesseract traineddata files to the target path if they don't already exist.

    Args:
        target_dir: The path to the target directory where the traineddata files will
            be copied to.
    """
    if not target_dir:
        return

    if target_dir.is_dir() and list(target_dir.glob("*.traineddata")):
        return

    if info.is_flatpak():
        src_path = Path("/app/share/tessdata")
    elif info.is_briefcase_package():
        src_path = info.get_resources_path() / "tessdata"
    else:
        return

    target_dir.mkdir(parents=True, exist_ok=True)
    for file_ in src_path.glob("*.*"):
        shutil.copy(file_, target_dir / file_.name)


def prepare() -> None:
    """Prepare environment variables depending on setup and system.

    Enable exiting via CTRL+C in Terminal.
    """
    # Allow closing QT app with CTRL+C in terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    if info.display_manager_is_wayland():
        _set_environ_for_wayland()
    if info.is_flatpak():
        _set_environ_for_flatpak()
    if info.is_appimage_package():
        _set_environ_for_appimage()
