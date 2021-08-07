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
        help="set capture mode to 'raw' or 'parse'",
    )
    parser.add_argument(
        "-l",
        "--language",
        type=str,
        help="set language(s) for text recognition, e.g. 'eng' or 'eng+deu'",
    )
    parser.add_argument(
        "-c", "--color", type=str, help="set primary color for UI, e.g. 'FF2E88'"
    )
    parser.add_argument(
        "-n",
        "--notification",
        help="disable or enable notification after ocr detection with '0' or '1' ",
        type=bool,
    )
    parser.add_argument(
        "-t",
        "--tray",
        help="disable or enable system tray with '0' or '1'",
        type=bool,
    )
    parser.add_argument(
        "-u",
        "--update",
        help="disable or enable check for updates with '0' or '1'",
        type=bool,
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
