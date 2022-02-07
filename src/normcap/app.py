"""Main application entry point."""

import locale
import logging
import os
import signal
import sys
from importlib import metadata, resources

# TODO: Manual test multi screen
# TODO: Streamline Logging
# TODO: Get rid of PySide6 for OCR
# TODO: Save debug images
# TODO: Test exception hook
# TODO: Improve test coverage
# TODO: Slim down packages

# Workaround for older tesseract version 4.0.0 on e.g. Debian Buster
locale.setlocale(locale.LC_ALL, "C")

# Some overrides when running in briefcase package
# TODO: Make testable function
package = sys.modules["__main__"].__package__
if package and "Briefcase-Version" in metadata.metadata(package):
    if sys.platform == "linux":
        # Use bundled tesseract binary
        with resources.as_file(resources.files("normcap")) as normcap_path:
            tesseract_path = normcap_path.parent.parent / "bin" / "tesseract"
            os.environ["TESSERACT_CMD"] = str(tesseract_path.resolve())

    elif sys.platform == "win32":
        with resources.as_file(resources.files("normcap.resources")) as resource_path:
            # Add openssl shipped with briefcase package to path
            openssl_path = resource_path / "openssl"
            os.environ["PATH"] += os.pathsep + str(openssl_path.resolve())

            # Use bundled tesseract binary
            tesseract_path = resource_path / "tesseract" / "tesseract.exe"
            os.environ["TESSERACT_CMD"] = str(tesseract_path.resolve())
            os.environ["TESSERACT_VERSION"] = "5.0.0"

from PySide6 import QtCore, QtWidgets

from normcap import __version__
from normcap.args import create_argparser
from normcap.gui import system_info, utils
from normcap.gui.main_window import MainWindow

logging.basicConfig(
    format="%(asctime)s - %(levelname)-7s - %(name)s:%(lineno)d - %(message)s",
    datefmt="%H:%M:%S",
    level="WARNING",
)


def main():
    """Start main application logic."""
    logger = logging.getLogger("normcap")
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

    logger.debug("System info:\n%s", system_info.to_dict())

    MainWindow(vars(args)).show()
    sys.exit(app.exec_())
