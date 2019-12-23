"""Runtime hook used by build.py to set env vars on Linux and Windows.

Building with Github Action on Linux fails due to unavailable fonts. Setting
the env fixes it.

Building on Windows requires tesseract's langague data folder to be
available as env.
"""

# Default
import os
import sys

if sys.platform.lower().startswith("linux"):
    os.environ["FONTCONFIG_PATH"] = (
        sys._MEIPASS + os.sep + "fonts"  # pylint: disable=no-member
    )

if sys.platform.lower().startswith("win"):
    os.environ["TESSDATA_PREFIX"] = (
        sys._MEIPASS + os.sep + "tessdata"  # pylint: disable=no-member
    )
