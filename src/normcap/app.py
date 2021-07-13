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
from normcap.utils import get_config_directory
from normcap.window_main import WindowMain

CONFIG_FILE = get_config_directory() / "normcap" / "config.yaml"


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
        args["languages"] = args["languages"].split("+")

    args["notifications"] = not args.pop("no_notifications")

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

        exclude_args = ["-v", "-V", "--verbose", "--very-verbose"]
        count_args = len([s for s in sys.argv if s not in exclude_args])
        if count_args > 1:
            config = Config(file_path=None, **args)
            logger.debug("Using unpersisted config (from cli args)")
        else:
            config = Config(file_path=CONFIG_FILE)
            logger.debug("Using persisted config (from config file)")

        logger.debug(f"Applied user config:{config}")

        window = WindowMain(config, system_info)
        window.show()

        sys.exit(app.exec_())
