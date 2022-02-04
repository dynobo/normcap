"""Main application entry point."""

import locale
import logging
import os
import signal
import sys
from importlib import resources

# Workaround for older tesseract version 4.0.0 on e.g. Debian Buster
locale.setlocale(locale.LC_ALL, "C")

# Add shipped openssl to path
if sys.platform == "win32":
    openssl_path = resources.files("normcap.resources").joinpath("openssl")
    os.environ["PATH"] += os.pathsep + str(openssl_path.absolute())

from PySide6 import QtCore, QtWidgets

from normcap import __version__, system_info
from normcap.args import create_argparser
from normcap.gui import utils
from normcap.gui.main_window import MainWindow

logging.basicConfig(
    format="%(asctime)s - %(levelname)-7s - %(name)s:%(lineno)d - %(message)s",
    datefmt="%H:%M:%S",
    level="WARNING",
)

# TODO: Overall wrap exceptions with FILE ISSUE hint


def main():
    """Start main application logic."""
    logger = logging.getLogger("normcap")
    # Application wide exception hook
    sys.excepthook = utils.hook_exceptions

    # Allow closing QT app with CTRL+C in terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    args = create_argparser().parse_args()
    if args.verbose:
        logger.setLevel("INFO")
    if args.very_verbose:
        logger.setLevel("DEBUG")

    logger.info("Start NormCap v%s", __version__)

    # QT has 32 as default cursor size on wayland, while it should be 24
    if "XCURSOR_SIZE" not in os.environ and system_info.display_manager_is_wayland():
        logger.debug("Setting XCURSOR_SIZE=24")
        os.environ["XCURSOR_SIZE"] = "24"

    QtCore.qInstallMessageHandler(utils.qt_log_wrapper)
    utils.copy_tessdata_files_to_config_dir()

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    logger.debug("System info:\n%s", system_info.to_string())

    MainWindow(vars(args)).show()
    sys.exit(app.exec_())
