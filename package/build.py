import argparse
import sys

from platforms.linux_briefcase import LinuxBriefcase
from platforms.linux_nuitka import LinuxNuitka
from platforms.macos_nuitka import MacNuitka
from platforms.windows_nuitka import WindowsNuitka

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Package NormCap", description="Create prebuild packages of Normcap."
    )
    parser.add_argument(
        "--framework",
        required=True,
        action="store",
        choices=["nuitka", "briefcase"],
        help="Select python bundling framework.",
    )
    args = parser.parse_args()

    if sys.platform.startswith("win"):
        builder = WindowsNuitka if args.framework == "nuitka" else None

    elif sys.platform.startswith("darwin"):
        builder = MacNuitka if args.framework == "nuitka" else None

    elif sys.platform.startswith("linux"):
        builder = LinuxNuitka if args.framework == "nuitka" else LinuxBriefcase

    builder().create()
