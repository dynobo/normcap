"""Define CLI arguments."""

import argparse


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
        "-m",
        "--mode",
        type=str,
        default="parse",
        help="set capture mode to 'raw' or 'parse'",
    )
    parser.add_argument(
        "-l",
        "--languages",
        type=str,
        default="eng",
        help="set language(s) for text recognition, e.g. eng+deu",
    )
    parser.add_argument(
        "-c", "--color", type=str, default="#FF2E88", help="set primary color for UI"
    )
    parser.add_argument(
        "-n",
        "--no-notifications",
        action="store_true",
        help="disable notifications shown after ocr detection",
        default=False,
    )
    parser.add_argument(
        "-t",
        "--tray",
        action="store_true",
        help="keep running in system tray - experimental",
        default=False,
    )
    parser.add_argument(
        "-u",
        "--updates",
        action="store_true",
        help="search for updates on startup - experimental",
        default=False,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print debug information to console",
        default=False,
    )
    parser.add_argument(
        "-V",
        "--very-verbose",
        action="store_true",
        help="print more debug information to console",
        default=False,
    )
    return parser
