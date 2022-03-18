"""Main application entry point."""

import locale
import logging
import os
import signal
import sys
from importlib import metadata, resources

# Workaround for older tesseract version 4.0.0 on e.g. Debian Buster
locale.setlocale(locale.LC_ALL, "C")

# Some overrides when running in briefcase package
def _set_environ_for_briefcase():
    package = sys.modules["__main__"].__package__
    if package and "Briefcase-Version" in metadata.metadata(package):
        if sys.platform == "linux":
            # Use bundled tesseract binary
            with resources.as_file(resources.files("normcap")) as normcap_path:
                tesseract_path = normcap_path.parent.parent / "bin" / "tesseract"
                os.environ["TESSERACT_CMD"] = str(tesseract_path.resolve())

        if sys.platform == "darwin":
            # Use bundled tesseract binary
            with resources.as_file(resources.files("normcap")) as normcap_path:
                tesseract_path = (
                    normcap_path.parent.parent / "app_packages" / "tesseract"
                )
                os.environ["TESSERACT_CMD"] = str(tesseract_path.resolve())

        elif sys.platform == "win32":
            with resources.as_file(
                resources.files("normcap.resources")
            ) as resource_path:
                # Add openssl shipped with briefcase package to path
                openssl_path = resource_path / "openssl"
                os.environ["PATH"] += os.pathsep + str(openssl_path.resolve())

                # Use bundled tesseract binary
                tesseract_path = resource_path / "tesseract" / "tesseract.exe"
                os.environ["TESSERACT_CMD"] = str(tesseract_path.resolve())
                os.environ["TESSERACT_VERSION"] = "5.0.0"


_set_environ_for_briefcase()

from PySide6 import QtCore, QtWidgets

from normcap import __version__
from normcap.args import create_argparser
from normcap.gui import system_info, utils
from normcap.gui.tray import SystemTray

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

    logger.setLevel(args.verbosity.upper())
    logger.info("Start NormCap v%s", __version__)

    if system_info.display_manager_is_wayland():
        # QT has 32 as default cursor size on wayland, while it should be 24
        if "XCURSOR_SIZE" not in os.environ:
            logger.debug("Set XCURSOR_SIZE=24")
            os.environ["XCURSOR_SIZE"] = "24"
        # Select wayland extension for better rendering
        if "QT_QPA_PLATFORM" not in os.environ:
            logger.debug("Set QT_QPA_PLATFORM=wayland")
            os.environ["QT_QPA_PLATFORM"] = "wayland"

    # Wrap QT logging output
    QtCore.qInstallMessageHandler(utils.qt_log_wrapper)

    if system_info.is_briefcase_package():
        utils.copy_tessdata_files_to_config_dir()

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    logger.debug("System info:\n%s", system_info.to_dict())

    tray = SystemTray(app, vars(args))
    tray.setVisible(True)

    sys.exit(app.exec_())
