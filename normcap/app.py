"""Start main application logic."""

import logging
import os
import signal
import sys
from argparse import Namespace
from pathlib import Path
from typing import NoReturn

from PySide6 import QtCore, QtWidgets

from normcap import __version__, utils
from normcap.gui import system_info
from normcap.gui.application import NormcapApp

logger = logging.getLogger(__name__)


def _get_args() -> Namespace:
    """Parse command line arguments.

    Exit if NormCap was started with --version flag.

    Auto-enable tray for "background mode", which starts NormCap in tray without
    immediately opening the select-region window.
    """
    args = utils.create_argparser().parse_args()

    if args.version:
        print(f"NormCap {__version__}")  # noqa: T201
        sys.exit(0)

    if args.background_mode:
        # Background mode requires tray icon
        args.tray = True

    return args


def _prepare_logging(log_level: str, log_file: Path | None = None) -> None:
    """Initialize the logger with the given log level.

    This function wraps the QT logger to control the output in the Python logger.
    For all log levels except DEBUG, an exception hook is used to improve the stack
    trace output for bug reporting on Github.

    Args:
        log_level: Valid Python log level (debug, warning, error)
        log_file: Target for saving log to file
    """
    sys.excepthook = utils.hook_exceptions

    utils.init_logger(log_level=log_level.upper(), log_file=log_file)
    logger = logging.getLogger("normcap")
    logger.info("Start NormCap v%s", __version__)

    # Wrap QT logging output
    QtCore.qInstallMessageHandler(utils.qt_log_wrapper)


def _prepare_envs() -> None:
    """Prepare environment variables depending on setup and system.

    Enable exiting via CTRL+C in Terminal.
    """
    # Allow closing QT app with CTRL+C in terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Silence opencv warnings
    os.environ["OPENCV_LOG_LEVEL"] = "OFF"

    if system_info.display_manager_is_wayland():
        utils.set_environ_for_wayland()
    if system_info.is_flatpak():
        utils.set_environ_for_flatpak()
    if system_info.is_appimage_package():
        utils.set_environ_for_appimage()


def _init_normcap() -> QtWidgets.QApplication:
    """Prepares the application.

    This does not call app.exec() to simplify testing.

    Returns:
        NormcapApp instance.
    """
    args = _get_args()

    _prepare_logging(
        log_level=str(getattr(args, "verbosity", "ERROR")),
        log_file=getattr(args, "log_file", Path.cwd() / "normcap.log"),
    )
    _prepare_envs()

    if system_info.is_prebuilt_package():
        tessdata_path = system_info.get_tessdata_path(
            config_directory=system_info.config_directory(),
            is_briefcase_package=system_info.is_briefcase_package(),
            is_flatpak_package=system_info.is_flatpak(),
        )
        utils.copy_traineddata_files(target_dir=tessdata_path)

    return NormcapApp(args=vars(args))


def run() -> NoReturn:
    """Run the main application."""
    sys.exit(_init_normcap().exec())


if __name__ == "__main__":
    run()
