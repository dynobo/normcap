import argparse
import sys

from platforms.linux_briefcase import LinuxBriefcase
from platforms.macos_briefcase import MacBriefcase
from platforms.windows_briefcase import WindowsBriefcase
from platforms.windows_briefcase_zip import WindowsBriefcaseZip

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Package NormCap", description="Create prebuilt packages of Normcap."
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Development build with version 0.0.1.",
    )
    args = parser.parse_args()

    builders = []
    if sys.platform == "win32":
        builders.append(WindowsBriefcase)
        builders.append(WindowsBriefcaseZip)

    elif sys.platform == "darwin":
        builders.append(MacBriefcase)

    elif sys.platform == "linux":
        builders.append(LinuxBriefcase)

    else:
        raise RuntimeError(f"Unknown platform '{sys.platform}'.")

    for builder in builders:
        builder().create()
