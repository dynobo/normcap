"""Main application entry point."""
import logging
import signal
import sys

from normcap import __version__, utils
from normcap.gui import system_info
from normcap.gui.tray import SystemTray
from PySide6 import QtCore, QtWidgets


def main() -> None:
    """Start main application logic."""
    args = utils.create_argparser().parse_args()
    if args.version:
        sys.exit(0)

    # Allow closing QT app with CTRL+C in terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    if args.verbosity.upper() != "DEBUG":
        sys.excepthook = utils.hook_exceptions

    utils.init_logger(level=args.verbosity.upper())
    logger = logging.getLogger("normcap")
    logger.info("Start NormCap v%s", __version__)

    # Wrap QT logging output
    QtCore.qInstallMessageHandler(utils.qt_log_wrapper)

    # Prepare environment
    if system_info.get_prebuild_package_type():
        utils.set_environ_for_prebuild_package()
    if system_info.display_manager_is_wayland():
        utils.set_environ_for_wayland()
    if system_info.is_flatpak_package():
        utils.set_environ_for_flatpak()
    if system_info.get_prebuild_package_type() or system_info.is_flatpak_package():
        utils.copy_tessdata_files_to_config_dir()

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    logger.debug("System info:\n%s", system_info.to_dict())

    tray = SystemTray(app, vars(args))
    tray.setVisible(True)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
