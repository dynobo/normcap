"""
"""
# Default
import logging
from logging.config import fileConfig

# Own
from normcap.capture import Capture
from normcap.data_model import Selection
from normcap.ocr import Ocr
from normcap.utils import log_dataclass

# Extra
import pyperclip


if __name__ == "__main__":
    # Setup logging
    fileConfig("logging.ini")
    logger = logging.getLogger(__name__)

    selection = Selection()
    cap = Capture()
    cap.capture_screen()
    cap.select_region_with_gui()
    cap.crop_shot()
    selection = cap.selection

    ocr = Ocr()
    selection.line_boxes = ocr.recognize(selection.image)

    log_dataclass(selection)

    pyperclip.copy(selection.text)
