# Standard
import argparse

# Own
from normcap.app import main


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
        description="Intelligent OCR-powered screen-capture tool "
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
        default="trigger",
        help="startup mode [raw,parse,trigger]",
    )
    parser.add_argument(
        "-l", "--lang", type=str, default="eng", help="set language for ocr tool"
    )
    parser.add_argument(
        "-c", "--color", type=str, default="#FF0000", help="set primary color for UI"
    )
    parser.add_argument(
        "-p", "--path", type=str, default=None, help="set a path for storing images"
    )
    return parser


if __name__ == "__main__":
    # Parse CLI args
    arg_parser = create_argparser()
    args = vars(arg_parser.parse_args())
    main(args=args)
