import argparse
import sys

from platforms.linux_briefcase import LinuxBriefcase
from platforms.linux_nuitka import LinuxNuitka
from platforms.macos_briefcase import MacBriefcase
from platforms.macos_nuitka import MacNuitka
from platforms.windows_briefcase import WindowsBriefcase
from platforms.windows_nuitka import WindowsNuitka

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Package NormCap", description="Create prebuild packages of Normcap."
    )
    parser.add_argument(
        "--framework",
        action="store",
        choices=["nuitka", "briefcase"],
        default="briefcase",
        help="Select python bundling framework.",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Development build with version 0.0.1.",
    )
    args = parser.parse_args()

    if sys.platform.startswith("win"):
        builder = WindowsNuitka if args.framework == "nuitka" else WindowsBriefcase

    elif sys.platform.startswith("darwin"):
        builder = MacNuitka if args.framework == "nuitka" else MacBriefcase

    elif sys.platform.startswith("linux"):
        builder = LinuxNuitka if args.framework == "nuitka" else LinuxBriefcase

    builder().create()
