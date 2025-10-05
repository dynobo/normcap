import argparse
import sys

from platforms.linux_briefcase import LinuxBriefcase
from platforms.macos_briefcase import MacBriefcase
from platforms.windows_briefcase import WindowsBriefcase
from platforms.windows_briefcase_zip import WindowsBriefcaseZip

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Package NormCap", description="Create prebuilt packages of NormCap."
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Development build with version 0.0.1.",
    )
    args = parser.parse_args()

    match sys.platform:
        case "win32":
            WindowsBriefcase().create()
            WindowsBriefcaseZip().create()

        case "darwin":
            MacBriefcase().create()

        case "linux":
            LinuxBriefcase().create()

        case _:
            raise RuntimeError(f"Unknown platform '{sys.platform}'.")
