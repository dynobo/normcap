"""
"""
# Default
import logging
from logging.config import fileConfig

# Own
from normcap.capture import Capture
from normcap.data_model import Selection
from normcap.ocr import Ocr

# Extra


if __name__ == "__main__":
    # Setup logging
    fileConfig("logging.ini")
    logger = logging.getLogger()

    selection = Selection()
    cap = Capture()
    # rect = cap.getRectangle()
    # print(rect)
    cap.capture_screen()
    cap.select_region_with_gui()
    cap.crop_shot()
    selection = cap.selection

    ocr = Ocr()
    selection.line_boxes = ocr.recognize(selection.image)

    print("+" * 30)
    print(selection.text())
    print("+" * 30)
    for k, v in vars(cap.selection).items():
        if not k.startswith("_"):
            print(f"{k}:{v}")
