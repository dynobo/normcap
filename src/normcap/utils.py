import argparse
import logging
import os
import sys

from normcap.gui import system_info
from normcap.gui.constants import DEFAULT_SETTINGS, DESCRIPTION

logger = logging.getLogger("normcap")


def create_argparser() -> argparse.ArgumentParser:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(prog="normcap", description=DESCRIPTION)

    for setting in DEFAULT_SETTINGS:
        if not setting.cli_arg:
            continue
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
        help="Reset all settings to default values",
        default=False,
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        default="warning",
        action="store",
        choices=["error", "warning", "info", "debug"],
        help="Set level of detail for console output (default: %(default)s)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print NormCap version and exit",
    )
    return parser


def set_environ_for_wayland() -> None:
    # QT has 32 as default cursor size on wayland, while it should be 24
    if "XCURSOR_SIZE" not in os.environ:
        logger.debug("Set XCURSOR_SIZE=24")
        os.environ["XCURSOR_SIZE"] = "24"

    # Select wayland extension for better rendering
    if "QT_QPA_PLATFORM" not in os.environ:
        logger.debug("Set QT_QPA_PLATFORM=wayland")
        os.environ["QT_QPA_PLATFORM"] = "wayland"


def set_environ_for_flatpak() -> None:
    # Unity DE (and maybe others) use gtk-nocsd to remove client side decorations.
    # It doesn't work within FlatPak, and the error message make pytesseract crash.
    # Therefore we deactivate it within the Flatpak.
    # See: https://github.com/dynobo/normcap/issues/290#issuecomment-1289629427
    ld_preload = os.environ.get("LD_PRELOAD", "")
    if "nocsd" in ld_preload.lower():
        logger.warning(
            "Found LD_PRELOAD='%s'. Setting to LD_PRELOAD='' to avoid issues.",
            ld_preload,
        )
        os.environ["LD_PRELOAD"] = ""


# Some overrides when running in prebuild package
def set_environ_for_prebuild_package() -> None:
    package = system_info.get_prebuild_package_type()

    if package not in ["nuitka", "briefcase"]:
        return

    if sys.platform == "linux":
        if package == "nuitka":
            # resources are currently not resolved on linux by nuitka:
            # https://github.com/Nuitka/Nuitka/issues/1451
            # Workround with using __file__
            tesseract_path = system_info.get_resources_path() / "tesseract"
            tesseract_bin = tesseract_path / "tesseract"
            ld_library_path = (
                f"{os.environ.get('LD_LIBRARY_PATH', '')}:{tesseract_path.resolve()}"
            )
            os.environ["LD_LIBRARY_PATH"] = ld_library_path
            os.environ["TESSERACT_CMD"] = str(tesseract_bin.resolve())
        elif package == "briefcase":
            bin_path = system_info.get_resources_path().parent.parent.parent / "bin"
            tesseract_path = bin_path / "tesseract"
            os.environ["TESSERACT_CMD"] = str(tesseract_path.resolve())
            os.environ["PATH"] = (
                f"{bin_path.absolute().resolve()}:" + os.environ["PATH"]
            )

    elif sys.platform == "darwin":
        if package == "nuitka":
            tesseract_bin = system_info.get_resources_path() / "tesseract" / "tesseract"
        elif package == "briefcase":
            tesseract_bin = (
                system_info.get_resources_path().parent.parent.parent
                / "app_packages"
                / "tesseract"
            )
        os.environ["TESSERACT_CMD"] = str(tesseract_bin.resolve())

    elif sys.platform == "win32":
        tesseract_bin = system_info.get_resources_path() / "tesseract" / "tesseract.exe"
        os.environ["TESSERACT_CMD"] = str(tesseract_bin.resolve())
        os.environ["TESSERACT_VERSION"] = "5.0.0"

    else:
        raise RuntimeError(f"Unsupported platform {sys.platform}")


def init_logger(level: str = "WARNING") -> None:
    log_format = "%(asctime)s - %(levelname)-7s - %(name)s:%(lineno)d - %(message)s"
    datefmt = "%H:%M:%S"
    logging.basicConfig(format=log_format, datefmt=datefmt)
    logger.setLevel(level)
