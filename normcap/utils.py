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
_XCB_ERROR_URL = (
    "https://github.com/dynobo/normcap/blob/main/FAQ.md"
    + "#linux-could-not-load-the-qt-platform-plugin-xcb",
)


def create_argparser() -> argparse.ArgumentParser:
    """Parse command line arguments."""
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
            help=setting.help,
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
        os.environ["PATH"] = binary_path + ":" + os.environ["PATH"]


def set_environ_for_flatpak() -> None:
    # Unity DE (and maybe others) use gtk-nocsd to remove client side decorations.
    # It doesn't work within FlatPak, and the error message make pytesseract crash.
    # Therefore we deactivate it within the Flatpak.
    # See: https://github.com/dynobo/normcap/issues/290#issuecomment-1289629427
    ld_preload = os.environ.get("LD_PRELOAD", "")
    if "nocsd" in ld_preload.lower():
        logger.warning(
            "Found LD_PRELOAD='%s'. Setting to LD_PRELOAD='' to avoid issues.",
            ld_preload,
        )
        os.environ["LD_PRELOAD"] = ""


def init_logger(level: str = "WARNING") -> None:
    log_format = "%(asctime)s - %(levelname)-7s - %(name)s:%(lineno)d - %(message)s"
    datefmt = "%H:%M:%S"
    logging.basicConfig(format=log_format, datefmt=datefmt)
    logger.setLevel(level)


def _redact_by_key(local_vars: dict) -> dict:
    """Replace potentially pi values."""
    filter_vars = [
        "tsv_data",
        "words",
        "self",
        "text",
        "transformed",
        "v",
    ]
    redacted = "REDACTED"
    for func_vars in local_vars.values():
        for f in filter_vars:
            if f in func_vars:
                func_vars[f] = redacted
        for k, v in func_vars.items():
            for attribute in ["ocr_text", "words", "parsed"]:
                if hasattr(v, attribute):
                    setattr(func_vars[k], attribute, redacted)
    return local_vars


def _get_local_vars(exc_traceback: Optional[TracebackType]) -> dict:
    local_vars = {}
    while exc_traceback:
        name = exc_traceback.tb_frame.f_code.co_name
        local_vars[name] = exc_traceback.tb_frame.f_locals
        exc_traceback = exc_traceback.tb_next
    return _redact_by_key(local_vars)


def _format_dict(d: dict) -> str:
    return pprint.pformat(d, compact=True, width=80, depth=2, indent=3, sort_dicts=True)


def hook_exceptions(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: Optional[TracebackType],
) -> None:  # sourcery skip: extract-method
    """Print traceback and quit application.

    TODO: Think about removing/simplifying exception hook after switch to Python 3.11
    """
    try:
        logger.critical("Uncaught exception! Quitting NormCap!")

        formatted_exc = "".join(
            f"  {e}" for e in traceback.format_exception_only(exc_type, exc_value)
        )
        formatted_tb = "".join(traceback.format_tb(exc_traceback))
        local_vars = _get_local_vars(exc_traceback)

        message = "\n### System:\n```\n"
        message += _format_dict(system_info.to_dict())
        message += "\n```\n\n### Variables:\n```"
        message += _format_dict(local_vars)
        message += "\n```\n\n### Exception:\n"
        message += f"```\n{formatted_exc}```\n"
        message += "\n### Traceback:\n"
        message += f"```\n{formatted_tb}```\n"

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
    """Intercept QT message.

    Used to hide away unnecessary warnings by showing them only on higher
    log level (--verbosity debug).
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
        logger.error("Try solving the problem as described here: %s", _XCB_ERROR_URL)
        logger.error("If that doesn't help, please open an issue: %s", _ISSUES_URLS)


def copy_traineddata_files(target_path: Optional[os.PathLike]) -> None:
    if not target_path:
        return

    target_path = Path(target_path)
    if target_path.is_dir() and list(target_path.glob("*.traineddata")):
        return

    if system_info.is_flatpak_package():
        src_path = Path("/app/share/tessdata")
    elif system_info.is_briefcase_package():
        src_path = system_info.get_resources_path() / "tessdata"
    else:
        return

    target_path.mkdir(parents=True, exist_ok=True)
    for f in src_path.glob("*.*"):
        shutil.copy(f, target_path / f.name)
