"""
"""

# Extra
import pyocr

# Own
from handlers.abstract_handler import AbstractHandler
from data_model import NormcapData
from utils import log_dataclass


class OcrHandler(AbstractHandler):
    def handle(self, request: NormcapData) -> NormcapData:
        self._logger.info("Applying OCR...")

        tool = self.get_tool()
        request.cli_args.language = self.get_language(request.cli_args.language, tool)

        # Actual OCR
        request.line_boxes = tool.image_to_string(
            request.image,
            lang=request.cli_args.language,
            builder=pyocr.builders.LineBoxBuilder(),
        )

        self._logger.debug("Dataclass after OCR:")
        log_dataclass(request)

        if self._next_handler:
            return super().handle(request)
        else:
            return request

    def get_tool(self):
        # Check available OCR
        ocr_tools = pyocr.get_available_tools()
        if len(ocr_tools) == 0:
            self._logger.error("No OCR tool found!")
            raise RuntimeError

        # The ocr tools are returned in the recommended order
        tool = ocr_tools[0]
        self._logger.info(f"Selecting '{tool.get_name()}' to perform ocr")
        return tool

    def get_language(self, lang, tool):
        # Check Language
        langs = tool.get_available_languages()
        if lang not in langs:
            self._logger.warn(f"Language {lang} for ocr not found!")
            self._logger.warn(f"Available languages: { {*langs} }.")
            self._logger.warn(f"Fallback to {langs[0]}.")
            lang = langs[0]

        self._logger.info(f"Using language '{lang}' for ocr")
        return lang
