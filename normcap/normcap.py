"""Main program logic."""

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


def parse_cli_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        argparse.Namespace -- CLI switches and (default) values
    """
    # Parse cli args
    arg_parser = argparse.ArgumentParser(
        prog="normcap",
        description="Intelligent screencapture tool to capture information instead of images",
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
        help="set default mode [raw, parse, trigger]",
    )
    arg_parser.add_argument(
        "-l",
        "--language",
        type=str,
        default="eng",
        help="set language for ocr tool (must be installed!)",
    )
    arg_parser.add_argument(
        "-c",
        "--color",
        type=str,
        default="red",
        help="set color for border and selection tool",
    )
    arg_parser.add_argument(
        "-p",
        "--path",
        type=str,
        default="",
        help="set a path to store cropped and original images",
    )
    return arg_parser.parse_args()


def init_logging(log_level: int) -> logging.Logger:
    """Initialize Logger with formatting and desired level.

    Arguments:
        log_level {logging._Level} -- Desired loglevel

    Returns:
        logging.Logger -- Formatted logger with desired level
    """
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
    if args.verbose:
        logger = init_logging(logging.DEBUG)
    else:
        logger = init_logging(logging.WARN)

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
