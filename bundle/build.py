import argparse
import sys

from platforms.linux_briefcase import LinuxBriefcase
from platforms.macos_briefcase import MacBriefcase
from platforms.windows_briefcase import WindowsBriefcase

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Package NormCap", description="Create prebuild packages of Normcap."
    )
    parser.add_argument(
        "--framework",
        action="store",
        choices=["briefcase"],
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
        builder = WindowsBriefcase

    elif sys.platform.startswith("darwin"):
        builder = MacBriefcase

    elif sys.platform.startswith("linux"):
        builder = LinuxBriefcase

    builder().create()
