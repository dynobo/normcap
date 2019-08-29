"""
"""

# Default
import logging

# Extra
import pyocr


class Ocr:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ocr_tools = pyocr.get_available_tools()
        if len(self.ocr_tools) == 0:
            self.logger.error("No OCR tool found!")
            raise RuntimeError

        # The ocr tools are returned in the recommended order
        self.tool = self.ocr_tools[0]
        self.logger.info(f"Selecting '{self.tool.get_name()}' to perform ocr")

        langs = self.tool.get_available_languages()
        self.logger.debug(f"Available languages for ocr: { {*langs} }")

        lang = langs[0]  # Not sorted!
        self.logger.info(f"Using language '{lang}' for ocr")

    def recognize(self, image):
        line_and_word_boxes = self.tool.image_to_string(
            image, lang="deu", builder=pyocr.builders.LineBoxBuilder()
        )
        return line_and_word_boxes
