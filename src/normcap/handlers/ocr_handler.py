"""Detect OCR tool & language and perform OCR on selected part of image."""

# Extra
import pyocr

# Own
from normcap.common.data_model import NormcapData
from normcap.common.utils import log_dataclass
from normcap.handlers.abstract_handler import AbstractHandler


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
