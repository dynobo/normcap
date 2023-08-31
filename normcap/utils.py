import argparse
import logging
import os
import pprint
import re
import shutil
import sys
import traceback
from pathlib import Path
from types import TracebackType
from typing import Optional

from PySide6 import QtCore

from normcap.gui import system_info
from normcap.gui.settings import DEFAULT_SETTINGS

logger = logging.getLogger("normcap")


_ISSUES_URLS = "https://github.com/dynobo/normcap/issues"
_XCB_ERROR_URL = "https://dynobo.github.io/normcap/#faqs-couldnt-load-platform-plugin"


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

    # Adopt PATH to find wl-copy if not installed on system (FlatPak brings its own)
    if system_info.is_briefcase_package() and not shutil.which("wl-copy"):
        binary_path = str((Path(__file__).parent.parent.parent / "bin").resolve())
        logger.debug("Append path to wl-copy to PATH+=%s", binary_path)
        os.environ["PATH"] = binary_path + os.pathsep + os.environ.get("PATH", "")


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


def _redact_by_key(local_vars: dict) -> dict:
    """Redact sensitive information from the given local variables dictionary.

    Args:
        local_vars: A dictionary containing local variables.

    Returns:
        The input dictionary with redacted sensitive information.
    """
    sensitive_keys = [
        "tsv_data",
        "words",
        "self",
        "text",
        "transformed",
        "v",
    ]
    redacted_value = "REDACTED"

    for func_vars in local_vars.values():
        for key in sensitive_keys:
            if key in func_vars:
                func_vars[key] = redacted_value

        for var_name, var_value in func_vars.items():
            for attribute in ["ocr_text", "words", "parsed"]:
                if hasattr(var_value, attribute):
                    setattr(func_vars[var_name], attribute, redacted_value)

    return local_vars


def _get_local_vars(exc_traceback: TracebackType | None) -> dict:
    """Retrieve the local variables of the current stack frame.

    Potentially sensitive values are redacted.

    Args:
        exc_traceback: The traceback object representing the current stack frame.
            If `exc_traceback` is `None`, the function will return an empty dict.

    Returns:
        A dict containing names and values of the local variables.
    """
    local_vars = {}

    while exc_traceback:
        name = exc_traceback.tb_frame.f_code.co_name
        local_vars[name] = exc_traceback.tb_frame.f_locals
        exc_traceback = exc_traceback.tb_next

    return _redact_by_key(local_vars)


def _format_dict(d: dict) -> str:
    """Format a dictionary as a string representation.

    Args:
        d: The dictionary to be formatted.

    Returns:
        str: The string representation of the formatted dictionary.
    """
    return pprint.pformat(d, compact=True, depth=2, indent=2)


def hook_exceptions(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: Optional[TracebackType],
) -> None:
    """Print traceback and quit application.

    ONHOLD: Think about removing/simplifying exception hook after switch to Python 3.11
    """
    try:
        logger.critical("Uncaught exception! Quitting NormCap!")

        formatted_exc = "".join(
            f"  {e}" for e in traceback.format_exception_only(exc_type, exc_value)
        )
        formatted_tb = "".join(traceback.format_tb(exc_traceback))
        local_vars = _get_local_vars(exc_traceback)

        message = (
            "\n### System:\n"
            f"```\n{_format_dict(system_info.to_dict())}\n```\n"
            "\n### Variables:\n"
            f"```\n{_format_dict(local_vars)}\n```\n"
            "\n### Exception:\n"
            f"```\n{formatted_exc}```\n"
            "\n### Traceback:\n"
            f"```\n{formatted_tb}```\n"
        )

        message = re.sub(
            r"((?:home|users)[/\\])(\w+)([/\\])",
            r"\1REDACTED\3",
            message,
            flags=re.IGNORECASE,
        )
        print(message, file=sys.stderr, flush=True)  # noqa: T201

    except Exception:
        logger.critical(
            "Uncaught exception! Quitting NormCap! (debug output limited)",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    logger.critical("Please open an issue with the output above on %s", _ISSUES_URLS)
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

    if "opentype support missing for" in msg:
        return

    if (level == "qtfatalmsg") or ("could not load the qt platform" in msg):
        logger.error("[QT] %s - %s", level, msg)
    else:
        logger.debug("[QT] %s - %s", level, msg)

    if ("xcb" in msg) and ("it was found" in msg):
        logger.error(
            "Please check if installing additional dependencies might help, see: %s",
            _XCB_ERROR_URL,
        )
        logger.error("If that doesn't solve it, please open an issue: %s", _ISSUES_URLS)


def copy_traineddata_files(target_dir: os.PathLike | None) -> None:
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
