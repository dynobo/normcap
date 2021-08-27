"""
OCR-powered screen-capture tool to capture information instead of images.
"""
import locale
import os
import signal
import sys

import importlib_resources

# Workaround for older tesseract version 4.0.0 on e.g. Debian Buster
locale.setlocale(locale.LC_ALL, "C")

# Add shipped openssl to path
if sys.platform == "win32":
    with importlib_resources.path("normcap.resources", "openssl") as p:
        openssl_path = str(p.absolute())
    os.environ["PATH"] += os.pathsep + openssl_path

from PySide2 import QtCore, QtNetwork, QtWidgets

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

    logger.info("Start NormCap v%s", __version__)
    logger.debug("CLI command: %s", " ".join(sys.argv))
    logger.debug("QT LibraryPaths: %s", QtCore.QCoreApplication.libraryPaths())

    try:
        print(
            "QSslSocket: ",
            QtNetwork.QSslSocket.sslLibraryBuildVersionString(),
            QtNetwork.QSslSocket.supportsSsl(),
        )
    except Exception as e:  # pylint: disable=broad-except
        print(e)

    # Wrap qt log messages with own logger
    QtCore.qInstallMessageHandler(utils.qt_message_handler)

    utils.init_tessdata()

    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    logger.debug("System info:\n%s", system_info.to_string())

    window = MainWindow(args)
    window.show()

    sys.exit(app.exec_())
