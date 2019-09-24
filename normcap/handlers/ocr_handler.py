"""Detect OCR tool & language and perform OCR on selected part of image."""

# Extra
import pyocr

# Own
from handlers.abstract_handler import AbstractHandler
from data_model import NormcapData
from utils import log_dataclass


class OcrHandler(AbstractHandler):
    """Handles the text recognition task."""

    def handle(self, request: NormcapData) -> NormcapData:
        """Apply OCR on selected image section.

        Arguments:
            AbstractHandler {class} -- self
            request {NormcapData} -- NormCap's session data

        Returns:
            NormcapData -- Enriched NormCap's session data
        """
        self._logger.info("Applying OCR...")

        # tool = self.get_tool()
        tool = pyocr.tesseract
        request.cli_args["lang"] = self.get_language(request.cli_args["lang"], tool)

        # Actual OCR
        request.line_boxes = tool.image_to_string(
            request.image,
            lang=request.cli_args["lang"],
            builder=pyocr.builders.LineBoxBuilder(),
        )

        log_dataclass("Dataclass after OCR:", request)

        if self._next_handler:
            return super().handle(request)
        else:
            return request

    def get_tool(self):
        """Check availability of OCR tools and return best.

        Raises:
            RuntimeError: No supported OCR tool found

        Returns:
            pyocr.TOOL -- Best available tool for OCR
        """
        # Check available OCR
        ocr_tools = pyocr.get_available_tools()
        if len(ocr_tools) == 0:
            self._logger.error("No OCR tool found!")
            raise RuntimeError

        # The ocr tools are returned in the recommended order
        tool = ocr_tools[0]
        self._logger.info("Selecting %s to perform ocr", tool.get_name())
        return tool

    def get_language(self, lang, tool) -> str:
        """Select language to use for OCR.

        Arguments:
            lang {str} -- Prefered language as passed via CLI
            tool {pyocr.TOOL} -- Detected prefered OCR tool to use

        Returns:
            str -- actual language to use
        """
        # Check Language
        langs = tool.get_available_languages()
        if lang not in langs:
            self._logger.warning("Language %s for ocr not found!", langs)
            self._logger.warning("Available languages: %s.", f"{ {*langs} }")
            self._logger.warning("Fallback to %s.", langs[0])
            lang = langs[0]

        self._logger.info("Using language %s for ocr...", lang)
        return lang
