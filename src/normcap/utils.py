import argparse
import os
import sys
from importlib import metadata, resources

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


def is_prebuild_package():
    package = sys.modules["__main__"].__package__
    if package and "Briefcase-Version" in metadata.metadata(package):
        # Briefcase package
        return True

    if hasattr(sys.modules["__main__"], "__compiled__"):
        # Nuitka package
        return True

    return False


# Some overrides when running in prebuild package
def set_environ_for_prebuild_package():

    if not is_prebuild_package():
        return

    if sys.platform == "linux":
        with resources.as_file(resources.files("normcap.resources")) as resource_path:
            tesseract_libs = resource_path.parent / "resources" / "tesseract"
            tesseract_bin = tesseract_libs / "tesseract"
            os.environ["LD_LIBRARY_PATH"] = str(tesseract_libs.resolve())
            os.environ["TESSERACT_CMD"] = str(tesseract_bin.resolve())

    if sys.platform == "darwin":
        with resources.as_file(resources.files("normcap")) as normcap_path:
            tesseract_bin = normcap_path.parent.parent / "app_packages" / "tesseract"
            os.environ["TESSERACT_CMD"] = str(tesseract_bin.resolve())

    elif sys.platform == "win32":
        with resources.as_file(resources.files("normcap.resources")) as resource_path:
            # TODO: Check if this is still necessary:
            # Add openssl shipped with briefcase package to path
            openssl_path = resource_path / "openssl"
            os.environ["PATH"] += os.pathsep + str(openssl_path.resolve())

            # Use bundled tesseract binary
            tesseract_bin = resource_path / "tesseract" / "tesseract.exe"
            os.environ["TESSERACT_CMD"] = str(tesseract_bin.resolve())
            os.environ["TESSERACT_VERSION"] = "5.0.0"
