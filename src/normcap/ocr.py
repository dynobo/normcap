"""Detect OCR tool & language and perform OCR on selected part of image."""

import csv
import statistics
from typing import List, Set

from PySide2 import QtGui

from normcap.logger import logger
from normcap.models import Capture, SystemInfo
from normcap.utils import tesserocr


class PerformOcr:
    """Handles the text recognition task."""

    languages: Set[str]
    tessdata_path: str

    def __call__(self, languages: List[str], capture: Capture, system_info: SystemInfo):
        """Apply OCR on selected image section.
        Arguments:
            AbstractHandler {class} -- self
            request {Capture} -- NormCap's session data
        Returns:
            Capture -- Enriched NormCap's session data
        """
        self.tessdata_path = system_info.tessdata_path
        self.languages = self.sanatize_language(
            languages, system_info.tesseract_languages
        )

        # TODO: Tessdata Path empty?
        logger.debug(f"Using tessdata in '{self.tessdata_path}'")
        logger.info(f"Using language '{self.languages}'")

        capture = self.extract(capture)
        return capture

    def extract(self, capture: Capture) -> Capture:
        """Recognize text in image and return structured dict."""

        if not isinstance(capture.image, QtGui.QImage):
            raise TypeError("No image for OCR available!")

        # OSD_ONLY: Orientation and script detection (OSD) only.
        # AUTO_OSD: Automatic page segmentation with orientation & script detection.
        # AUTO_ONLY: Automatic page segmentation, but no OSD, or OCR.
        # AUTO: Fully automatic page segmentation, but no OSD. (`tesserocr` default)
        # SINGLE_COLUMN: Assume a single column of text of variable sizes.
        # SINGLE_BLOCK_VERT_TEXT: Assume a  uniform block of vertically aligned text.
        # SINGLE_BLOCK: Assume a single uniform block of text.
        # SINGLE_LINE: Treat the image as a single text line.
        # SINGLE_WORD: Treat the image as a single word.
        # CIRCLE_WORD: Treat the image as a single word in a circle.
        # SINGLE_CHAR: Treat the image as a single character.
        # SPARSE_TEXT: Find as much text as possible in no particular order.
        # SPARSE_TEXT_OSD: Sparse text with orientation and script det.
        # RAW_LINE: Treat the image as a single text line, bypassing Tesseract hacks.
        # COUNT: Number of enum entries.
        psm_opt = tesserocr.PSM.AUTO_OSD

        # TESSERACT_ONLY: Run Tesseract only - fastest
        # LSTM_ONLY: Run just the LSTM line recognizer. (>=v4.00)
        # TESSERACT_LSTM_COMBINED: Run the LSTM recognizer, but allow fallback
        #     to Tesseract when things get difficult. (>=v4.00)
        # CUBE_ONLY: Specify this mode when calling Init*(), to indicate that
        #     any of the above modes should be automatically inferred from the
        #     variables in the language-specific config, command-line configs, or
        #     if not specified in any of the above should be set to the default
        #     `OEM.TESSERACT_ONLY`.
        # TESSERACT_CUBE_COMBINED: Run Cube only - better accuracy, but slower.
        # DEFAULT: Run both and combine results - best accuracy.
        oem_opt = tesserocr.OEM.LSTM_ONLY

        with tesserocr.PyTessBaseAPI(
            path=self.tessdata_path,
            lang="+".join(list(self.languages)),
            oem=oem_opt,
            psm=psm_opt,
        ) as api:
            # api.SetImage(capture.image)
            # imagedata, int width, int height,
            # int bytes_per_pixel, int bytes_per_line)
            img = capture.image
            api.SetImageBytes(
                bytes(img.constBits()),
                img.width(),
                img.height(),
                img.depth() // 8,
                img.bytesPerLine(),
            )
            tsv_data = api.GetTSVText(0)
        words = self.tsv_to_list_of_dicts(tsv_data)

        mean_conf = statistics.mean([w.get("conf", 0) for w in words] + [0])
        logger.info(
            f"PSM Mode: {psm_opt}, OSM Mode: {oem_opt}, "
            + f"Mean Conf: {mean_conf:.2f}"
        )

        capture.words = words
        capture.psm_opt = psm_opt

        return capture

    def extract_best(self, img, lang) -> Capture:
        """Recognize text in image and return structured dict."""

        # Workaround for a pyinstaller bug on Windows:
        img.format = "PNG"

        psm_opts = [2, 4, 6, 7]

        best_psm = 0  # For diagnostics
        best_mean_conf = 0
        best_words: list = []

        for psm_opt in psm_opts:
            # OCR
            with tesserocr.PyTessBaseAPI(
                lang=lang, oem=tesserocr.OEM.LSTM_ONLY, psm=psm_opt
            ) as api:
                api.SetImage(img)
                tsv_data = api.GetTSVText(0)
            words = self.tsv_to_list_of_dicts(tsv_data)

            # Calc confidence, store best
            mean_conf = statistics.mean([w.get("conf", 0) for w in words] + [0])
            logger.info("PSM Mode: %s, Mean Conf: %s", psm_opt, mean_conf)
            if mean_conf > best_mean_conf:
                best_mean_conf = mean_conf
                best_words = words
                best_psm = psm_opt

        logger.info("Best PSM Mode: %s", best_psm)
        capture = Capture(words=best_words, psm_opt=best_psm)
        logger.debug("Capture after OCR:%s", capture)

        return capture

    @staticmethod
    def tsv_to_list_of_dicts(tsv_data) -> list:
        """Convert tab separated values to list of dicts."""
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

        # Read tsv to list of dicts
        words = list(
            csv.DictReader(
                tsv_data.splitlines(),
                fieldnames=tsv_columns,
                delimiter="\t",
                quoting=csv.QUOTE_NONE,
            )
        )

        # Cast types
        for idx, word in enumerate(words):
            for key, value in word.items():
                if key != "text":
                    words[idx][key] = int(value)  # type: ignore # (casting on purpose)

        # Filter empty words
        words = [w for w in words if w["text"].strip()]
        return words

    @staticmethod
    def sanatize_language(
        config_languages: List[str], tesseract_languages: List[str]
    ) -> Set[str]:
        """Retrieve tesseract version number."""
        set_config_languages = set(config_languages)
        set_tesseract_languages = set(tesseract_languages)
        unavailable_langs = set_config_languages.difference(set_tesseract_languages)
        available_langs = set_config_languages.intersection(set_tesseract_languages)

        if not unavailable_langs:
            return set_config_languages

        logger.warning(
            f"Languages {unavailable_langs} not found. "
            + f"Available on the system are: {set_tesseract_languages}"
        )
        if available_langs:
            logger.warning(f"Fallback to languages {available_langs}")
            return available_langs

        fallback_language = set_tesseract_languages.pop()
        logger.warning(f"Fallback to language {fallback_language}")
        return set([fallback_language])


perform_ocr = PerformOcr()
