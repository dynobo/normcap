"""
OCR-powered screen-capture tool to capture information instead of images.
"""
import locale

# Workaround for older tesseract version 4.0.0 on e.g. Debian Buster
locale.setlocale(locale.LC_ALL, "C")

import signal
import sys

from PySide2 import QtCore, QtWidgets

from normcap import __version__, system_info, utils
from normcap.args import create_argparser
from normcap.gui.main_window import MainWindow
from normcap.logger import logger


def main():
    """Main entry point."""

    sys.excepthook = utils.except_hook
    # Allow to close QT app with CTRL+C in terminal:
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    args = vars(create_argparser().parse_args())
    if args.get("verbose", False):
        logger.setLevel("INFO")
    if args.get("very_verbose", False):
        logger.setLevel("DEBUG")

    logger.info(f"Starting NormCap v{__version__}")
    logger.debug(f"CLI command: {' '.join(sys.argv)}")
    logger.debug(f"QT LibraryPaths: {QtCore.QCoreApplication.libraryPaths()}")

    # Wrap qt log messages with own logger
    QtCore.qInstallMessageHandler(utils.qt_message_handler)

    utils.init_tessdata()

    # TODO: Check if still needed / other solution
    # with utils.temporary_environ(XCURSOR_SIZE=24):
    app = QtWidgets.QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    app.setQuitOnLastWindowClosed(False)

    logger.debug(f"System info: {system_info.to_string()}")

    window = MainWindow(args)
    window.show()

    sys.exit(app.exec_())
