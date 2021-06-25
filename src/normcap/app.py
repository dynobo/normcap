"""
 OCR-powered screen-capture tool to capture information instead of images.
"""
import locale

# Workaround for older tesseract version 4.0.0 on e.g. Debian Buster
locale.setlocale(locale.LC_ALL, "C")

import sys

from PySide2 import QtCore, QtWidgets

from normcap import __version__, utils
from normcap.args import create_argparser
from normcap.logger import logger
from normcap.models import Config
from normcap.window_main import WindowMain


def main():
    """Main entry point."""
    sys.excepthook = utils.except_hook

    arg_parser = create_argparser()
    args = vars(arg_parser.parse_args())

    if args.pop("verbose"):
        logger.setLevel("INFO")
    if args.pop("very_verbose"):
        logger.setLevel("DEBUG")

    if args["languages"]:
        args["languages"] = set(args["languages"].split("+"))

    logger.info(f"Starting Normcap v{__version__}")

    # QtCore.QCoreApplication.addLibraryPath()
    lib_paths = QtCore.QCoreApplication.libraryPaths()
    logger.debug(f"QT LibraryPaths: {lib_paths}")

    # Start Qt Application
    with utils.temporary_environ(XCURSOR_SIZE=24):
        QtCore.qInstallMessageHandler(utils.qt_message_handler)

        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        app = QtWidgets.QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        # Screen info needs to be gathered _after_ app is instanciated
        system_info = utils.get_system_info()
        logger.debug(f"Detected system info:{system_info}")

        config = Config(**args)
        logger.debug(f"Applied user config:{config}")

        window = WindowMain(config, system_info)
        window.show()

        sys.exit(app.exec_())
