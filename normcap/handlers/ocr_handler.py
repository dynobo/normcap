"""Detect OCR tool & language and perform OCR on selected part of image."""

# Default
import csv
import statistics

# Extra
from tesserocr import PyTessBaseAPI, OEM  # type: ignore # pylint: disable=no-name-in-module

# Own
from normcap.common.data_model import NormcapData
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

        self._logger.debug("Dataclass after OCR:%s", request)

        if self._next_handler:
            return super().handle(request)

        return request

    def img_to_dict(self, img, lang) -> list:
        if not img.size or img.size[0] * img.size[1] <= 25:
            self._logger.info(
                "Selected region of %s too small for OCR. Skipping.", img.size
            )
            return []

        img.format = "PNG"  # WORKAROUND for a pyinstaller bug on Win

        # 0 = Orientation and script detection (OSD) only.
        # 1 = Automatic page segmentation with OSD.
        # 2 = Automatic page segmentation, but no OSD, or OCR
        # 3 = Fully automatic page segmentation, but no OSD. (Default)
        # 4 = Assume a single column of text of variable sizes.
        # 5 = Assume a single uniform block of vertically aligned text.
        # 6 = Assume a single uniform block of text.
        # 7 = Treat the image as a single text line.
        # 8 = Treat the image as a single word.
        # 9 = Treat the image as a single word in a circle.
        # 10 = Treat the image as a single character.
        psm_opt = 2

        with PyTessBaseAPI(lang=lang, oem=OEM.LSTM_ONLY, psm=psm_opt) as api:
            api.SetImage(img)
            tsv_data = api.GetTSVText(0)
        words = self.tsv_to_list_of_dicts(tsv_data)

        mean_conf = statistics.mean([w.get("conf", 0) for w in words] + [0])
        self._logger.info("PSM Mode: %s, Mean Conf: %s", psm_opt, mean_conf)
        return words

    def img_to_dict_best(self, img, lang) -> list:
        img.format = "PNG"  # WORKAROUND for a pyinstaller bug on Win

        # 0 = Orientation and script detection (OSD) only.
        # 1 = Automatic page segmentation with OSD.
        # 2 = Automatic page segmentation, but no OSD, or OCR
        # 3 = Fully automatic page segmentation, but no OSD. (Default)
        # 4 = Assume a single column of text of variable sizes.
        # 5 = Assume a single uniform block of vertically aligned text.
        # 6 = Assume a single uniform block of text.
        # 7 = Treat the image as a single text line.
        # 8 = Treat the image as a single word.
        # 9 = Treat the image as a single word in a circle.
        # 10 = Treat the image as a single character.
        PSM_OPTS = [2, 4, 6, 7]

        best_psm = 0  # For diagnostics
        best_mean_conf = 0
        best_words: list = []

        for psm_opt in PSM_OPTS:
            # OCR
            with PyTessBaseAPI(lang=lang, oem=OEM.LSTM_ONLY, psm=psm_opt) as api:
                api.SetImage(img)
                tsv_data = api.GetTSVText(0)
            words = self.tsv_to_list_of_dicts(tsv_data)

            # Calc confidence, store best
            mean_conf = statistics.mean([w.get("conf", 0) for w in words] + [0])
            self._logger.info("PSM Mode: %s, Mean Conf: %s", psm_opt, mean_conf)
            if mean_conf > best_mean_conf:
                best_mean_conf = mean_conf
                best_words = words
                best_psm = psm_opt

        self._logger.info("Best PSM Mode: %s", best_psm)
        return best_words

    def tsv_to_list_of_dicts(self, tsv_data) -> list:
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
                tsv_data.split("\n"),
                fieldnames=tsv_columns,
                delimiter="\t",
                quoting=csv.QUOTE_NONE,
            )
        )

        # Cast types
        for idx, word in enumerate(words):
            for k, v in word.items():
                if k != "text":
                    words[idx][k] = int(v)  # type: ignore # (casting on purpose)

        # Filter empty words
        words = [w for w in words if w["text"].strip()]
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
            tesseract_langs = api.GetAvailableLanguages()

        requested_langs = lang.split("+")
        unavailable_langs = set(requested_langs).difference(set(tesseract_langs))
        available_langs = set(requested_langs).intersection(set(tesseract_langs))

        if unavailable_langs:
            self._logger.warning("Language %s for ocr not found!", {*unavailable_langs})
            self._logger.warning("Available tesseract langs: %s.", {*tesseract_langs})
            if available_langs:
                lang = "+".join([rl for rl in requested_langs if rl in available_langs])
            else:
                lang = tesseract_langs[0]
            self._logger.warning("Fallback to %s.", lang)

        self._logger.info("Using language %s for ocr...", lang)
        return lang
