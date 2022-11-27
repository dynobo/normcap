"""Main application entry point."""
import logging
import signal
import sys
from argparse import Namespace

from normcap import __version__, utils
from normcap.gui import system_info
from normcap.gui.tray import SystemTray
from PySide6 import QtCore, QtWidgets


def _get_args() -> Namespace:
    """Start main application logic."""
    args = utils.create_argparser().parse_args()
    if args.version:
        print(f"NormCap {__version__}")  # noqa: T201
        sys.exit(0)
    return args


def _prepare_logging(args: Namespace) -> None:
    if args.verbosity.upper() != "DEBUG":
        sys.excepthook = utils.hook_exceptions

    utils.init_logger(level=args.verbosity.upper())
    logger = logging.getLogger("normcap")
    logger.info("Start NormCap v%s", __version__)

    # Wrap QT logging output
    QtCore.qInstallMessageHandler(utils.qt_log_wrapper)


def _prepare_envs() -> None:
    """Prepare environment variables depending on setup and system."""
    # Allow closing QT app with CTRL+C in terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    if system_info.get_prebuild_package_type():
        utils.set_environ_for_prebuild_package()
    if system_info.display_manager_is_wayland():
        utils.set_environ_for_wayland()
    if system_info.is_flatpak_package():
        utils.set_environ_for_flatpak()
    if system_info.get_prebuild_package_type() or system_info.is_flatpak_package():
        utils.copy_tessdata_files_to_config_dir()


def main() -> None:
    args = _get_args()
    _prepare_logging(args)
    _prepare_envs()

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray = SystemTray(app, vars(args))
    tray.setVisible(True)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
