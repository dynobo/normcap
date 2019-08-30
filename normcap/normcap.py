"""
"""
# Default
import logging
import argparse
import pathlib
import datetime

# Extra
import pyperclip

# Own
from capture import Capture
from crop import Crop
from data_model import Selection
from ocr import Ocr
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


def _store_images(path, images):
    storage_path = pathlib.Path(path)
    now = datetime.datetime.now()

    for idx, image in enumerate(images):
        name = f"{now:%Y-%m-%d_%H:%M}_{idx}.png"
        image.save(storage_path / name)


def main():
    args = parse_cli_args()

    # Setup logging
    if args.verbose:
        logger = init_logging(logging.DEBUG)
    else:
        logger = init_logging(logging.WARN)

    logger.info("Creating data object...")
    selection = Selection(cli_args=args)

    logger.info("Taking screenshot(s)...")
    selection = Capture().capture_screen(selection)

    logger.info("Launching gui for selection...")
    selection = Crop().select_and_crop(selection)

    if selection.cli_args.path:
        logger.info("Saving images to {selection.cli_args.path}...")
        images = [selection.image] + [s["image"] for s in selection.shots]
        _store_images(selection.cli_args.path, images)

    log_dataclass(selection)
    return

    ocr = Ocr()
    selection.line_boxes = ocr.recognize(selection.image)

    log_dataclass(selection)

    pyperclip.copy(selection.text)


if __name__ == "__main__":
    main()
