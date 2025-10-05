import logging
import os
import re
import sys
from pathlib import Path
from types import TracebackType

from PySide6 import QtCore

from normcap import __version__
from normcap.gui import system_info

logger = logging.getLogger(__name__)

_ISSUES_URLS = "https://github.com/dynobo/normcap/issues/new"


class ShortenPathnameFilter(logging.Filter):
    """Filter to shorten log record pathname from absolute to relative."""

    _root_path_length = len(str(Path(__file__).parent.resolve())) + 1

    def filter(self, record: logging.LogRecord) -> bool:
        record.pathname = record.pathname[self._root_path_length :]
        return True


def _is_wayland_display_manager() -> bool:
    xdg_session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    has_wayland_display_env = bool(os.environ.get("WAYLAND_DISPLAY", ""))
    return "wayland" in xdg_session_type or has_wayland_display_env


def _init_logger(log_level: str = "WARNING", log_file: Path | None = None) -> None:
    """Initializes a logger with a specified log level."""
    log_format = "%(asctime)s - %(levelname)-7s - %(pathname)s:%(lineno)d - %(message)s"
    datefmt = "%H:%M:%S"

    handlers: list[logging.Handler] = []

    stream_handler = logging.StreamHandler()
    stream_handler.addFilter(ShortenPathnameFilter())
    handlers.append(stream_handler)

    # On Windows, stream handler output is not visible. Therefore, we log to file on
    # desktop, if the level was set to more detailed than Warning (the default).
    if (
        log_file is None
        and sys.platform == "win32"
        and logging.getLevelName(log_level) < logging.WARNING
    ):
        log_file = system_info.desktop_dir() / "normcap.log"

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode="w")
        file_handler.addFilter(ShortenPathnameFilter())
        handlers.append(file_handler)

    logging.basicConfig(
        format=log_format,
        datefmt=datefmt,
        handlers=handlers,
        level=log_level,
        force=True,
    )
    logger.setLevel(level=log_level)


def _hook_exceptions(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
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


def _qt_log_wrapper(
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


def prepare_logging(log_level: str, log_file: Path | None = None) -> None:
    """Initialize the logger with the given log level.

    This function wraps the QT logger to control the output in the Python logger.
    For all log levels except DEBUG, an exception hook is used to improve the stack
    trace output for bug reporting on Github.

    Args:
        log_level: Valid Python log level (debug, warning, error)
        log_file: Target for saving log to file
    """
    sys.excepthook = _hook_exceptions

    _init_logger(log_level=log_level.upper(), log_file=log_file)
    logger = logging.getLogger(__name__)
    logger.info("Start NormCap v%s", __version__)

    # Wrap QT logging output
    QtCore.qInstallMessageHandler(_qt_log_wrapper)
