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
from .data_model import NormcapData
from .utils import log_dataclass
from .handlers.abstract_handler import Handler
from .handlers.capture_handler import CaptureHandler
from .handlers.crop_handler import CropHandler
from .handlers.store_handler import StoreHandler
from .handlers.ocr_handler import OcrHandler
from .handlers.clipboard_handler import ClipboardHandler
from .handlers.magic_handler import MagicHandler
from .handlers.enhance_img_handler import EnhanceImgHandler


VERSION = "0.1a0"


def create_argparser() -> argparse.ArgumentParser:
    """Parse command line arguments.

    Returns:
        ArgumentParser
    """

    class ArgFormatter(argparse.ArgumentDefaultsHelpFormatter):
        """Custom formatter to increase intendation of help output.

        Arguments:
            argparse -- argpase object
        """

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
    return arg_parser


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
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%H:%M:%S",
            level=log_level,
        )
    else:
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%H:%M:%S",
            level=log_level,
        )

    logger = logging.getLogger(__name__)
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


def main(test_data: NormcapData = None):
    """Main program logic."""

    # Init Logger
    logger = init_logging(logging.WARN, to_file=False)
    logger.info("Starting NormCap %s...", VERSION)

    # Parse CLI args
    arg_parser = create_argparser()

    if test_data and test_data.test_mode:
        logger.info("Running in test mode...")
        args = test_data.cli_args
        normcap_data = test_data
    else:
        logger.info("Parsing args and creating data object...")
        args = vars(arg_parser.parse_args())
        normcap_data = NormcapData(cli_args=args)

    # Set logging to verbose
    if args["verbose"]:
        logger = init_logging(logging.DEBUG, to_file=True)

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

    return normcap_data


if __name__ == "__main__":
    _ = main()
