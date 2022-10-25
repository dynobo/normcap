"""Main application entry point."""
import locale
import logging
import signal
import sys

# Workaround for older tesseract version 4.0.0 on e.g. Debian Buster
locale.setlocale(locale.LC_ALL, "C")

from PySide6 import QtCore, QtWidgets

from normcap import __version__
from normcap.gui import system_info, utils
from normcap.gui.tray import SystemTray
from normcap.utils import (
    create_argparser,
    init_logger,
    set_environ_for_flatpak,
    set_environ_for_prebuild_package,
    set_environ_for_wayland,
)


def main():
    """Start main application logic."""
    sys.excepthook = utils.hook_exceptions

    # Allow closing QT app with CTRL+C in terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    args = create_argparser().parse_args()
    if args.version:
        print(f"NormCap {__version__}")
        sys.exit(0)

    init_logger(level=args.verbosity.upper())
    logger = logging.getLogger("normcap")
    logger.info("Start NormCap v%s", __version__)

    # Wrap QT logging output
    QtCore.qInstallMessageHandler(utils.qt_log_wrapper)

    # Prepare environment
    if system_info.is_prebuild_package():
        set_environ_for_prebuild_package()
    if system_info.display_manager_is_wayland():
        set_environ_for_wayland()
    if system_info.is_flatpak_package():
        set_environ_for_flatpak()
    if system_info.is_prebuild_package() or system_info.is_flatpak_package():
        utils.copy_tessdata_files_to_config_dir()

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    logger.debug("System info:\n%s", system_info.to_dict())

    tray = SystemTray(app, vars(args))
    tray.setVisible(True)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
