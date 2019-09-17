"""Main program logic."""

# Workaround for PyInstaller + pyocr issue.
# (already fixed in pyocr master)
# TODO: Remove, after release, to avoid problems with real missing path
# import sys, os, pathlib

# if getattr(sys, "frozen", False):
#     os.environ["PATH"] += os.pathsep + sys._MEIPASS
#     dummy_dir = os.path.join(sys._MEIPASS, "data", "tessdata")
#    pathlib.Path(dummy_dir).mkdir(parents=True, exist_ok=True)

# Default
import logging
import argparse


# Own
from data_model import NormcapData
from utils import log_dataclass
from handlers.abstract_handler import Handler
from handlers.capture_handler import CaptureHandler
from handlers.crop_handler import CropHandler
from handlers.store_handler import StoreHandler
from handlers.ocr_handler import OcrHandler
from handlers.clipboard_handler import ClipboardHandler
from handlers.magic_handler import MagicHandler
from handlers.enhance_img_handler import EnhanceImgHandler


_VERSION = "0.1a0"


def parse_cli_args() -> dict:
    """Parse command line arguments.

    Returns:
        argparse.Namespace -- CLI switches and (default) values
    """

    class ArgFormatter(argparse.ArgumentDefaultsHelpFormatter):
        def __init__(self, prog):
            super().__init__(prog, max_help_position=30)

    arg_parser = argparse.ArgumentParser(
        prog="normcap",
        description="Intelligent OCR-powered screen-capture tool "
        + "to capture information instead of images.",
        formatter_class=ArgFormatter,
    )

    arg_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print debug information to console",
        default=False,
    )
    arg_parser.add_argument(
        "-m",
        "--mode",
        #
        type=str,
        default="trigger",
        help="startup mode [raw,parse,trigger]",
    )
    arg_parser.add_argument(
        "-l", "--lang", type=str, default="eng", help="set language for ocr tool"
    )
    arg_parser.add_argument(
        "-c", "--color", type=str, default="#FF0000", help="set primary color for UI"
    )
    arg_parser.add_argument(
        "-p", "--path", type=str, default=None, help="set a path for storing images"
    )
    return vars(arg_parser.parse_args())


def init_logging(log_level: int, to_file: bool = False) -> logging.Logger:
    """Initialize Logger with formatting and desired level.

    Arguments:
        log_level {logging._Level} -- Desired loglevel
        to_file {bool} -- Log also to file on disk

    Returns:
        logging.Logger -- Formatted logger with desired level
    """

    if to_file:
        logging.basicConfig(
            filename="normcap.log",
            filemode="w",
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
            level=log_level,
        )
    else:
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
            level=log_level,
        )

    logger = logging.getLogger(__name__)

    logger.info("Starting normcap...")
    return logger


def client_code(handler: Handler, normcap_data) -> NormcapData:
    """Wrapper around Chain of Responsibility classes.

    Arguments:
        handler {Handler} -- Most outer handler
        normcap_data {NormcapData} -- NormCap's session data

    Returns:
        NormcapData -- Enriched NormCap's session data
    """
    result = handler.handle(normcap_data)
    return result


def main():
    args = parse_cli_args()

    # Setup logging
    if args["verbose"]:
        logger = init_logging(logging.DEBUG, to_file=True)
    else:
        logger = init_logging(logging.WARN, to_file=False)

    logger.info(f"Starting NormCap {_VERSION}...")
    logger.info("Creating data object...")
    normcap_data = NormcapData(cli_args=args)

    # Define Handlers
    capture = CaptureHandler()
    crop = CropHandler()
    store = StoreHandler()
    enhance_img = EnhanceImgHandler()
    ocr = OcrHandler()
    clipboard = ClipboardHandler()
    magics = MagicHandler()

    # Define Chain of Responsibilities
    # fmt: off
    capture.set_next(crop) \
           .set_next(store) \
           .set_next(enhance_img) \
           .set_next(ocr) \
           .set_next(magics) \
           .set_next(clipboard)
    # fmt: on

    # Run chain
    normcap_data = client_code(capture, normcap_data)

    log_dataclass("Final data object:", normcap_data)


if __name__ == "__main__":
    main()
