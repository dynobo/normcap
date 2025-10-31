"""Start main application logic."""

import logging
import sys
from pathlib import Path
from typing import NoReturn

from PySide6 import QtWidgets

from normcap import argparser, environment
from normcap import logger_config as logger_
from normcap.gui.application import NormcapApp
from normcap.system import info

logger = logging.getLogger(__name__)


def _init_normcap() -> QtWidgets.QApplication:
    """Prepares the application.

    This does not call app.exec() to simplify testing.

    Returns:
        NormcapApp instance.
    """
    args = argparser.get_args()

    logger_.prepare_logging(
        log_level=str(getattr(args, "verbosity", "ERROR")),
        log_file=getattr(args, "log_file", Path.cwd() / "normcap.log"),
    )
    environment.prepare()

    if info.is_packaged():
        tessdata_path = info.get_tessdata_path(
            config_directory=info.config_directory(),
            is_packaged=info.is_packaged(),
        )
        environment.copy_traineddata_files(target_dir=tessdata_path)

    logger.debug("System info:\n%s", info.to_dict())
    return NormcapApp(args=vars(args))


def run() -> NoReturn:
    """Run the main application."""
    sys.exit(_init_normcap().exec())


if __name__ == "__main__":
    run()
