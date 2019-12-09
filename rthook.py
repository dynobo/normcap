import os
import sys

if sys.platform.lower().startswith("linux"):
    os.environ["FONTCONFIG_PATH"] = sys._MEIPASS + os.sep + "fonts"

if sys.platform.lower().startswith("win"):
    os.environ["TESSDATA_PREFIX"] = sys._MEIPASS + os.sep + "tessdata"
