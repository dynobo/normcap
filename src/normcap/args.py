"""Define CLI arguments."""
import argparse

from normcap.data import DEFAULT_SETTINGS, DESCRIPTION


def create_argparser() -> argparse.ArgumentParser:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(prog="normcap", description=DESCRIPTION)

    for setting in DEFAULT_SETTINGS:
        parser.add_argument(
            f"-{setting.flag}",
            f"--{setting.key}",
            type=setting.type_,
            help=setting.help,
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
