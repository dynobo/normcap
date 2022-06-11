import argparse
import os
import sys

from normcap.gui import system_info
from normcap.gui.constants import DEFAULT_SETTINGS, DESCRIPTION


def create_argparser() -> argparse.ArgumentParser:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(prog="normcap", description=DESCRIPTION)

    for setting in DEFAULT_SETTINGS:
        parser.add_argument(
            f"-{setting.flag}",
            f"--{setting.key}",
            type=setting.type_,
            help=setting.help,
            choices=setting.choices,
        )
    parser.add_argument(
        "-r",
        "--reset",
        action="store_true",
        help="reset all settings to default values",
        default=False,
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        default="warning",
        action="store",
        choices=["error", "warning", "info", "debug"],
        help="set level of detail for console output (default: %(default)s)",
    )
    return parser


# Some overrides when running in prebuild package
def set_environ_for_prebuild_package():

    if not system_info.is_prebuild_package():
        return

    if sys.platform == "linux":
        # resources are currently not resolved on linux by nuitka:
        # https://github.com/Nuitka/Nuitka/issues/1451
        # Workround with using __file__
        tesseract_path = system_info.get_resources_path() / "tesseract"
        tesseract_bin = tesseract_path / "tesseract"
        os.environ["LD_LIBRARY_PATH"] = str(tesseract_path.resolve())
        os.environ["TESSERACT_CMD"] = str(tesseract_bin.resolve())

    if sys.platform == "darwin":
        tesseract_bin = system_info.get_resources_path() / "tesseract" / "tesseract"
        os.environ["TESSERACT_CMD"] = str(tesseract_bin.resolve())

    elif sys.platform == "win32":
        tesseract_bin = system_info.get_resources_path() / "tesseract" / "tesseract.exe"
        os.environ["TESSERACT_CMD"] = str(tesseract_bin.resolve())
        os.environ["TESSERACT_VERSION"] = "5.0.0"
