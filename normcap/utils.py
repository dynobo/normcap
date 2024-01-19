import argparse
import logging
import os
import re
import shutil
import sys
from pathlib import Path
from types import TracebackType
from typing import Optional

from PySide6 import QtCore

from normcap.clipboard import Handler
from normcap.gui import system_info
from normcap.gui.settings import DEFAULT_SETTINGS

logger = logging.getLogger("normcap")


_ISSUES_URLS = "https://github.com/dynobo/normcap/issues/new"


def _is_wayland_display_manager() -> bool:
    xdg_session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    has_wayland_display_env = bool(os.environ.get("WAYLAND_DISPLAY", ""))
    return "wayland" in xdg_session_type or has_wayland_display_env


def create_argparser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        The configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="normcap",
        description=(
            "OCR-powered screen-capture tool to capture information instead of images."
        ),
    )

    for setting in DEFAULT_SETTINGS:
        if not setting.cli_arg:
            continue
        parser.add_argument(
            f"-{setting.flag}",
            f"--{setting.key}",
            type=setting.type_,
            help=setting.help_,
            choices=setting.choices,
            nargs=setting.nargs,
        )
    parser.add_argument(
        "-r",
        "--reset",
        action="store_true",
        help="Reset all settings to default values",
        default=False,
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        default="warning",
        action="store",
        choices=["error", "warning", "info", "debug"],
        help="Set level of detail for console output (default: %(default)s)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print NormCap version and exit",
    )
    parser.add_argument(
        "--cli-mode",
        action="store_true",
        help="Print text after detection to stdout and exits immediately",
    )
    parser.add_argument(
        "--background-mode",
        action="store_true",
        help="Start minimized to tray, without capturing",
    )
    parser.add_argument(
        "--clipboard-handler",
        action="store",
        choices=[h.name.lower() for h in Handler],
        help="Force using specific clipboard handler instead of auto-selecting",
    )
    return parser


def set_environ_for_wayland() -> None:
    # QT has 32 as default cursor size on wayland, while it should be 24
    if "XCURSOR_SIZE" not in os.environ:
        logger.debug("Set XCURSOR_SIZE=24")
        os.environ["XCURSOR_SIZE"] = "24"

    # Select wayland extension for better rendering
    if "QT_QPA_PLATFORM" not in os.environ:
        logger.debug("Set QT_QPA_PLATFORM=wayland")
        os.environ["QT_QPA_PLATFORM"] = "wayland"


def set_environ_for_appimage() -> None:
    # Append path to shipped binaries to PATH
    bin_path = str((Path(__file__).parent.parent.parent / "bin").resolve())
    logger.debug("Append %s to AppImage internal PATH", bin_path)
    os.environ["PATH"] = (
        os.environ.get("PATH", "").rstrip(os.pathsep) + os.pathsep + bin_path
    )


def set_environ_for_flatpak() -> None:
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


def init_logger(log_level: str = "WARNING") -> None:
    """Initializes a logger with a specified log level."""
    log_format = "%(asctime)s - %(levelname)-7s - %(name)s:%(lineno)d - %(message)s"
    datefmt = "%H:%M:%S"
    logging.basicConfig(format=log_format, datefmt=datefmt)
    logger.setLevel(log_level)


def hook_exceptions(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: Optional[TracebackType],
) -> None:
    """Print traceback and quit application."""
    logger.critical(
        "Uncaught exception!", exc_info=(exc_type, exc_value, exc_traceback)
    )
    logger.critical("System info: %s", system_info.to_dict())
    logger.critical(
        "Unfortunately, NormCap has to be terminated due to an unknown problem.\n"
        "Please help improve NormCap by reporting this error, including the output "
        "above, on\n%s\nThanks!",
        _ISSUES_URLS,
    )
    sys.exit(1)


def qt_log_wrapper(
    mode: QtCore.QtMsgType, _: QtCore.QMessageLogContext, message: str
) -> None:
    """Wrapper function for logging messages from the Qt framework.

    Used to hide away unnecessary warnings by showing them only on higher
    log level (--verbosity debug).

    Args:
        mode: The type of the log message.
        _: The log context, not used in this function.
        message: The log message.
    """
    level = mode.name.lower()
    msg = message.lower()

    if re.search("opentype support missing for", msg, re.IGNORECASE):
        return

    if (level == "qtfatalmsg") or ("could not load the qt platform" in msg):
        logger.error("[QT] %s - %s", level, msg)
    else:
        logger.debug("[QT] %s - %s", level, msg)

    if re.search("no qt platform plugin could be initialized", msg, re.IGNORECASE):
        if _is_wayland_display_manager():
            packages = (
                "- Arch/Manjaro: \n"
                "- Debian/Ubuntu/Mint: qt6-wayland\n"
                "- Fedora/CentOS: \n"
                "- OpenSuse: qt6-wayland\n"
            )
            packages = (
                "================================================\n"
                "DISTRO               | REQUIRED PACKAGES\n"
                "================================================\n"
                "Arch/Manjaro         | qt6-wayland\n"
                "Debian/Ubuntu/Mint   |\n"
                "OpenSuse             |\n"
                "------------------------------------------------\n"
                "Fedora/CentOS        | qt6-qtwayland\n"
                "------------------------------------------------\n"
            )
        else:
            packages = (
                "================================================\n"
                "DISTRO               | REQUIRED PACKAGES\n"
                "================================================\n"
                "Arch/Manjaro         | libxcb xcb-util-cursor\n"
                "Fedora/CentOS        |\n"
                "------------------------------------------------\n"
                "Debian/Ubuntu/Mint   | libxcb1 libxcb-cursor0\n"
                "OpenSuse             |\n"
                "------------------------------------------------\n"
            )
        message = (
            "NormCap crashed!\n\n"
            "NormCap could not be started, probably because of missing system "
            "dependencies!\n"
            "Please make sure you have the following system packages installed:\n\n"
            f"{packages}\n"
            "If that doesn't solve the problem, please report it via GitHub:\n"
            f"{_ISSUES_URLS}\n"
        )
        logger.error(message)


def copy_traineddata_files(target_dir: Optional[os.PathLike]) -> None:
    """Copy Tesseract traineddata files to the target path if they don't already exist.

    Args:
        target_dir: The path to the target directory where the traineddata files will
            be copied to.
    """
    if not target_dir:
        return

    target_dir = Path(target_dir)
    if target_dir.is_dir() and list(target_dir.glob("*.traineddata")):
        return

    if system_info.is_flatpak_package():
        src_path = Path("/app/share/tessdata")
    elif system_info.is_briefcase_package():
        src_path = system_info.get_resources_path() / "tessdata"
    else:
        return

    target_dir.mkdir(parents=True, exist_ok=True)
    for file_ in src_path.glob("*.*"):
        shutil.copy(file_, target_dir / file_.name)
