"""
"""
# Default
import logging
import argparse

# Extra
import pyperclip

# Own
from capture import Capture
from crop import Crop
from data_model import NormcapData
from ocr import Ocr
from utils import log_dataclass, store_images


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


def main():
    args = parse_cli_args()

    # Setup logging
    if args.verbose:
        logger = init_logging(logging.DEBUG)
    else:
        logger = init_logging(logging.WARN)

    logger.info("Creating data object...")
    normcap_data = NormcapData(cli_args=args)

    logger.info("Taking screenshot(s)...")
    normcap_data = Capture().capture_screen(normcap_data)

    logger.info("Launching gui for selection...")
    normcap_data = Crop().select_and_crop(normcap_data)

    if normcap_data.selected_area() < 400:
        logger.warn("Selected area is unreasonable small. Aborting...")
        return

    if normcap_data.cli_args.path:
        logger.info("Saving images to {selection.cli_args.path}...")
        images = [normcap_data.image] + [s["image"] for s in normcap_data.shots]
        store_images(normcap_data.cli_args.path, images)

    log_dataclass(normcap_data)
    return

    ocr = Ocr()
    normcap_data.line_boxes = ocr.recognize(normcap_data.image)

    log_dataclass(normcap_data)

    pyperclip.copy(normcap_data.text)


if __name__ == "__main__":
    main()
