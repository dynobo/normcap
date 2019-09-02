"""
"""
# Default
import logging
import argparse

# Own
from data_model import NormcapData
from handler import Handler
from capture import CaptureHandler
from crop import CropHandler
from store import StoreHandler
from ocr import OcrHandler
from clipboard import ClipboardHandler
from utils import log_dataclass


def parse_cli_args():
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
        default="raw",
        help="set default mode to [raw, parse, trigger]",
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


def init_logging(log_level):
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
        level=log_level,
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting normcap...")
    return logger


def client_code(handler: Handler, normcap_data) -> NormcapData:
    """
    The client code is usually suited to work with a single handler. In most
    cases, it is not even aware that the handler is part of a chain.
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
    ocr = OcrHandler()
    clipboard = ClipboardHandler()

    # Define Chain of Responsibilities
    capture.set_next(crop).set_next(store).set_next(ocr).set_next(clipboard)

    # Run chain
    normcap_data = client_code(capture, normcap_data)

    logger.info("Final data object:")
    log_dataclass(normcap_data)


if __name__ == "__main__":
    main()
