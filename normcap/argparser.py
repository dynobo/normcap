from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from normcap import __version__
from normcap.clipboard import Handler as ClipboardHandler
from normcap.gui.settings import DEFAULT_SETTINGS
from normcap.notification import Handler as NotificationHandler
from normcap.screenshot import Handler as ScreenshotHandler

if TYPE_CHECKING:
    from _typeshed import SupportsWrite


class _WindowsArgumentParser(argparse.ArgumentParser):
    """ArgumentParser variant that prints help to the Windows console.

    This is a workaround for the quirk of briefcase packaged GUI apps on Windows,
    where sys.stdout and sys.stderr are not available. Therefore, we use the CON
    device to directly write the help text to the console.
    """

    def print_help(self, file: SupportsWrite[str] | None = None) -> None:
        try:
            with Path("CON").open("w", encoding="utf-8") as console:
                console.write("\r\033[K")
                super().print_help(file=console)
                console.write("\r\n\r\nPress Enter to continue ...")
                console.flush()
        except Exception:  # noqa: S110  # except with pass
            pass


def _create_argparser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        The configured argument parser.
    """
    parser_cls: type[argparse.ArgumentParser] = argparse.ArgumentParser
    if sys.platform == "win32" and sys.stdout is None:
        # ONHOLD: After briefcase update: Check if workaround is still necessary
        parser_cls = _WindowsArgumentParser

    parser = parser_cls(
        prog="normcap",
        description=(
            "OCR-powered screen-capture tool to capture information instead of images."
        ),
    )

    for setting in DEFAULT_SETTINGS:
        if not setting.cli_arg:
            continue
        flags = (
            [f"-{setting.flag}", f"--{setting.key}"]
            if setting.flag
            else [f"--{setting.key}"]
        )
        parser.add_argument(
            *flags,
            type=setting.type_,
            help=setting.help_ + f" (default: {setting.value})",
            choices=setting.choices,
            nargs=setting.nargs,
        )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset all settings to default values",
        default=False,
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        default="warning",
        action="store",
        choices=["error", "warning", "info", "debug"],
        help="Set level of detail for console output (default: %(default)s)",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        action="store",
        help="Save console output to a file",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print NormCap version and exit",
    )
    parser.add_argument(
        "--cli-mode",
        action="store_true",
        help="Print text after detection to stdout and exits immediately",
    )
    parser.add_argument(
        "--background-mode",
        action="store_true",
        help="Start minimized to tray, without capturing",
    )
    parser.add_argument(
        "--screenshot-handler",
        action="store",
        choices=[h.name.lower() for h in ScreenshotHandler],
        help=(
            "Only relevant on Linux! Force using specific screenshot handler instead "
            "of auto-selecting"
        ),
    )
    parser.add_argument(
        "--clipboard-handler",
        action="store",
        choices=[h.name.lower() for h in ClipboardHandler],
        help="Force using specific clipboard handler instead of auto-selecting",
    )
    parser.add_argument(
        "--notification-handler",
        action="store",
        choices=[h.name.lower() for h in NotificationHandler],
        help=(
            "Only relevant on Linux! Force using specific notification handler instead "
            "of auto-selecting"
        ),
    )
    parser.add_argument(
        "--dbus-activation",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    return parser


def get_args() -> argparse.Namespace:
    """Parse command line arguments.

    Exit if NormCap was started with --version flag.

    Auto-enable tray for "background mode", which starts NormCap in tray without
    immediately opening the select-region window.
    """
    args = _create_argparser().parse_args()

    if args.version:
        print(f"NormCap {__version__}")  # noqa: T201
        sys.exit(0)

    if args.background_mode:
        # Background mode requires tray icon
        args.tray = True

    return args
