"""Start main application logic."""

import logging
import signal
import sys
from argparse import Namespace
from typing import NoReturn

from PySide6 import QtCore, QtWidgets

from normcap import __version__, utils
from normcap.gui import system_info
from normcap.gui.tray import SystemTray


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
        args.tray = True

    return args


def _prepare_logging(log_level: str) -> None:
    """Initialize the logger with the given log level.

    This function wraps the QT logger to control the output in the Python logger.
    For all log levels except DEBUG, an exception hook is used to improve the stack
    trace output for bug reporting on Github.

    Args:
        log_level: Valid Python log level (debug, warning, error)
    """
    sys.excepthook = utils.hook_exceptions

    utils.init_logger(log_level=log_level.upper())
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

    if system_info.display_manager_is_wayland():
        utils.set_environ_for_wayland()
    if system_info.is_flatpak_package():
        utils.set_environ_for_flatpak()
    if system_info.is_appimage_package():
        utils.set_environ_for_appimage()


def _get_application() -> QtWidgets.QApplication:
    """Get a QApplication instance that doesn't exit on window close."""
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app


def _prepare() -> tuple[QtWidgets.QApplication, SystemTray]:
    """Prepares the application and system tray without executing.

    Returns:
        A tuple containing the QApplication ready for execution
            and the not yet visible SystemTray.
    """
    args = _get_args()

    _prepare_logging(log_level=str(getattr(args, "verbosity", "ERROR")))
    _prepare_envs()

    if system_info.is_prebuilt_package():
        utils.copy_traineddata_files(target_dir=system_info.get_tessdata_path())

    app = _get_application()
    tray = SystemTray(app, vars(args))

    return app, tray


def run() -> NoReturn:
    """Run the main application."""
    app, tray = _prepare()
    tray.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
