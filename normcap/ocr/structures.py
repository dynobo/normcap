import enum
import os
from dataclasses import dataclass, field
from os import PathLike
from typing import Optional, Protocol

from PySide6.QtGui import QImage


@enum.unique
class PSM(enum.IntEnum):
    """Available tesseract mode options."""

    OSD_ONLY = 0  # Orientation and script detection (OSD) only.
    AUTO_OSD = 1  # Automatic page segmentation with orientation & script detection.
    AUTO_ONLY = 2  # Automatic page segmentation, but no OSD, or OCR.
    AUTO = 3  # Fully automatic page segmentation, but no OSD. (`tesserocr` default)
    SINGLE_COLUMN = 4  # Assume a single column of text of variable sizes.
    SINGLE_BLOCK_VERT_TEXT = 5  # Assume a  uniform block of vertically aligned text.
    SINGLE_BLOCK = 6  # Assume a single uniform block of text.
    SINGLE_LINE = 7  # Treat the image as a single text line.
    SINGLE_WORD = 8  # Treat the image as a single word.
    CIRCLE_WORD = 9  # Treat the image as a single word in a circle.
    SINGLE_CHAR = 10  # Treat the image as a single character.
    SPARSE_TEXT = 11  # Find as much text as possible in no particular order.
    SPARSE_TEXT_OSD = 12  # Sparse text with orientation and script det.
    RAW_LINE = 13  # Treat the image as a single text line, bypassing Tesseract hacks.
    COUNT = 14  # Number of enum entries.


@enum.unique
class OEM(enum.IntEnum):
    """Available tesseract model options."""

    TESSERACT_ONLY = 0  # Run Tesseract only - fastest
    LSTM_ONLY = 1  # Run just the LSTM line recognizer. (>=v4.00)
    TESSERACT_LSTM_COMBINED = 2  # Run the LSTM recognizer, but allow fallback
    # to Tesseract when things get difficult. (>=v4.00)
    DEFAULT = 3  # Run both and combine results - best accuracy.


class Transformer(enum.IntEnum):
    SINGLE_LINE = enum.auto()
    MULTI_LINE = enum.auto()
    PARAGRAPH = enum.auto()
    MAIL = enum.auto()
    URL = enum.auto()


@dataclass
class TessArgs:
    """Arguments used when evoking tesseract."""

    tessdata_path: Optional[PathLike]
    lang: str
    oem: OEM
    psm: PSM

    def as_list(self) -> list[str]:
        """Generate command line args for tesseract."""
        arg_list = [
            "-l",
            self.lang,
            "--oem",
            str(self.oem.value),
            "--psm",
            str(self.psm.value),
        ]
        if self.tessdata_path:
            arg_list.extend(["--tessdata-dir", str(self.tessdata_path)])
        if self.is_language_without_spaces():
            arg_list.extend(["-c", "preserve_interword_spaces=1"])
        return arg_list

    def is_language_without_spaces(self) -> bool:
        """Check if selected languages are only languages w/o spaces between words."""
        languages_without_spaces = {
            "chi_sim",
            "chi_sim_vert",
            "chi_tra",
            "chi_tra_vert",
            "jpn",
            "jpn_vert",
            "kor",
        }
        selected_languages = set(self.lang.split("+"))
        return selected_languages.issubset(languages_without_spaces)


@dataclass
class OcrResult:
    """Encapsulate recognized text and meta information."""

    tess_args: TessArgs
    words: list[dict]  # Words+metadata detected by OCR
    image: QImage
    transformer_scores: dict[Transformer, float] = field(default_factory=dict)
    parsed: str = ""  # Transformed result

    def _count_unique_sections(self, level: str) -> int:
        postfix = "_num"
        unique_sections = {w[level + postfix] for w in self.words}
        return len(unique_sections)

    @property
    def best_scored_transformer(self) -> Optional[Transformer]:
        """Transformer with highest score."""
        if self.transformer_scores:
            return max(
                self.transformer_scores, key=lambda k: self.transformer_scores[k]
            )
        return None

    @property
    def mean_conf(self) -> float:
        """Mean of ocr confidence."""
        if conf_values := [float(w.get("conf", 0)) for w in self.words]:
            return sum(conf_values) / len(conf_values)
        return 0

    @property
    def text(self) -> str:
        """Provides the resulting text of the OCR.

        If parsed text (compiled by a transformer) is available, return that one,
        otherwise fallback to "raw".
        """
        return self.parsed or self.add_linebreaks()

    def add_linebreaks(
        self,
        block_sep: str = os.linesep * 2,
        par_sep: str = os.linesep,
        line_sep: str = os.linesep,
        word_sep: str = " ",
    ) -> str:
        """OCR text as string with linebreaks.

        When default separators are used, the output should be equal to the output
        by Tesseract when run in CLI.
        """
        last_block_num = None
        last_par_num = None
        last_line_num = None
        text = ""

        for word in self.words:
            block_num = word.get("block_num", None)
            par_num = word.get("par_num", None)
            line_num = word.get("line_num", None)

            if block_num != last_block_num:
                text += block_sep + word["text"]
            elif par_num != last_par_num:
                text += par_sep + word["text"]
            elif line_num != last_line_num:
                text += line_sep + word["text"]
            else:
                text += word_sep + word["text"]

            last_block_num = block_num
            last_par_num = par_num
            last_line_num = line_num

        return text.strip()

    @property
    def num_chars(self) -> int:
        """Provide number of chars without word separators."""
        return sum(len(w["text"]) for w in self.words)

    @property
    def num_lines(self) -> int:
        """Provide number of lines in OCR text."""
        return self._count_unique_sections("line")

    @property
    def num_pars(self) -> int:
        """Provide number of paragraphs in OCR text."""
        return self._count_unique_sections("par")

    @property
    def num_blocks(self) -> int:
        """Provide number of text blocks in OCR text."""
        return self._count_unique_sections("block")


class TransformerProtocol(Protocol):
    """Transformer protocol."""

    def score(self, ocr_result: OcrResult) -> float:
        """Determines the likelihood of the transformer to fit to the ocr result.

        Arguments:
            ocr_result: Recognized text and meta information.

        Returns:
            score between 0-100 (100 = more likely).
            # TODO: Use a score 0-1 instead.
        """
        ...  # pragma: no cover

    def transform(self, ocr_result: OcrResult) -> str:
        """Apply a transformation to the detected text.

        Arguments:
            ocr_result: Recognized text and meta information.

        Returns:
            Transformed text.
        """
