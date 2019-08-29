"""
"""
# Default
import logging

# Own
from capture import Capture
from crop import Crop
from data_model import Selection
from ocr import Ocr
from utils import log_dataclass

# Extra
import pyperclip


def main():
    # Setup logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG,
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting normcap...")

    selection = Selection()

    selection = Capture().capture_screen(selection)

    selection = Crop().select_and_crop(selection)

    log_dataclass(selection)
    return
    # cap.select_region_with_gui()
    # cap.crop_shot()
    # selection = cap.selection

    ocr = Ocr()
    selection.line_boxes = ocr.recognize(selection.image)

    log_dataclass(selection)

    pyperclip.copy(selection.text)


if __name__ == "__main__":
    main()
