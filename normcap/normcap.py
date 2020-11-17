"""Main program logic."""

# Standard
import logging
import argparse

# Own
from normcap import __version__
from normcap.common.data_model import NormcapData
from normcap.handlers.abstract_handler import Handler
from normcap.handlers.capture_handler import CaptureHandler
from normcap.handlers.crop_handler import CropHandler
from normcap.handlers.store_handler import StoreHandler
from normcap.handlers.ocr_handler import OcrHandler
from normcap.handlers.clipboard_handler import ClipboardHandler
from normcap.handlers.magic_handler import MagicHandler
from normcap.handlers.enhance_img_handler import EnhanceImgHandler
from normcap.handlers.notification_handler import NotificationHandler


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

    parser = argparse.ArgumentParser(
        prog="normcap",
        description="OCR-powered screen-capture tool "
        + "to capture information instead of images.",
        formatter_class=ArgFormatter,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print debug information to console",
        default=False,
    )
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        default="parse",
        help="startup mode [raw,parse]",
    )
    parser.add_argument(
        "-l",
        "--lang",
        type=str,
        default="eng",
        help="languages for ocr, e.g. eng+deu",
    )
    parser.add_argument(
        "-c", "--color", type=str, default="#BF616A", help="set primary color for UI"
    )
    parser.add_argument(
        "-p", "--path", type=str, default=None, help="set a path for storing images"
    )
    return parser


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
    logger = init_logging(logging.INFO, to_file=False)
    logger.info("Starting NormCap v%s ...", __version__)

    # Init Normcap Data
    if test_data and test_data.test_mode:
        logger.info("Running in test mode...")
        args = test_data.cli_args
        normcap_data = test_data
    else:
        arg_parser = create_argparser()
        args = vars(arg_parser.parse_args())
        normcap_data = NormcapData(cli_args=args)

    # Set adjust loglevel
    if args["verbose"]:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.WARN)

    # Define Handlers
    capture = CaptureHandler()
    crop = CropHandler()
    enhance_img = EnhanceImgHandler()
    store = StoreHandler()
    ocr = OcrHandler()
    magics = MagicHandler()
    clipboard = ClipboardHandler()
    notification = NotificationHandler()

    # Define Chain of Responsibilities
    # fmt: off
    capture.set_next(crop) \
           .set_next(enhance_img) \
           .set_next(store) \
           .set_next(ocr) \
           .set_next(magics) \
           .set_next(clipboard) \
           .set_next(notification)
    # fmt: on

    # Run chain
    normcap_data = client_code(capture, normcap_data)

    logger.debug("Final data object:%s", normcap_data)

    return normcap_data


if __name__ == "__main__":
    _ = main()
