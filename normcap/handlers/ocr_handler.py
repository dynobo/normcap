"""Detect OCR tool & language and perform OCR on selected part of image."""

# Default
import csv


# Extra
from tesserocr import PyTessBaseAPI, OEM  # type: ignore # pylint: disable=no-name-in-module


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

        request.cli_args["lang"] = self.get_language(request.cli_args["lang"])

        # Actual OCR & transformation
        request.words = self.img_to_dict(request.image, request.cli_args["lang"])

        log_dataclass("Dataclass after OCR:", request)

        if self._next_handler:
            return super().handle(request)

        return request

    def img_to_dict(self, img, lang):
        # with PyTessBaseAPI(oem=OEM.LSTM_ONLY) as api:
        with PyTessBaseAPI(lang=lang, oem=OEM.DEFAULT) as api:
            api.SetImage(img)
            tsv_data = api.GetTSVText(0)

        tsv_columns = [
            "level",
            "page_num",
            "block_num",
            "par_num",
            "line_num",
            "word_num",
            "left",
            "top",
            "width",
            "height",
            "conf",
            "text",
        ]
        words = list(
            csv.DictReader(
                tsv_data.split("\n"), fieldnames=tsv_columns, delimiter="\t",
            )
        )
        words = [w for w in words if w["text"]]
        return words

    def get_language(self, lang) -> str:

        """Select language to use for OCR.

        Arguments:
            lang {str} -- Prefered language as passed via CLI

        Returns:
            str -- actual language to use
        """
        # Check Language
        with PyTessBaseAPI(lang=lang) as api:
            langs = api.GetAvailableLanguages()

        if lang not in langs:
            self._logger.warning("Language %s for ocr not found!", langs)
            self._logger.warning("Available languages: %s.", f"{ {*langs} }")
            self._logger.warning("Fallback to %s.", langs[0])
            lang = langs[0]

        self._logger.info("Using language %s for ocr...", lang)
        return lang
