import os
import statistics
from dataclasses import dataclass, field
from enum import IntEnum
from os import PathLike
from typing import Optional

from packaging import version
from PIL import Image


@dataclass
class TessArgs:
    """Arguments used when envoking tesseract."""

    path: PathLike
    lang: str
    oem: int
    psm: int
    version: version.Version


@dataclass
class OcrResult:
    """Encapsulates recognized text and meta information."""

    tess_args: TessArgs
    words: list[dict]  # Words+metadata detected by OCR
    image: Image.Image
    magic_scores: dict[str, float] = field(default_factory=dict)  # magics with scores
    transformed: str = ""  # Transformed result

    def _count_unique_sections(self, level: str) -> int:
        postfix = "_num"
        unique_sections = {w[level + postfix] for w in self.words}
        return len(unique_sections)

    @property
    def best_scored_magic(self) -> Optional[str]:
        """Magic with highest score."""
        if not self.magic_scores:
            return None
        return max(self.magic_scores, key=lambda k: self.magic_scores[k])

    @property
    def mean_conf(self) -> float:
        """Mean of ocr confidence."""
        if conf_values := [float(w.get("conf", 0)) for w in self.words]:
            return statistics.mean(conf_values)
        return 0

    @property
    def text(self) -> str:
        """OCR text as single line string."""
        raw_text = " ".join(w["text"].strip() for w in self.words).strip()
        return self.transformed or raw_text

    @property
    def lines(self) -> str:
        """OCR text as multi line string."""
        current_line_num = 0
        all_lines = []
        for word in self.words:
            if word["line_num"] != current_line_num:
                current_line_num = word["line_num"]
                all_lines.append(word["text"])
            else:
                all_lines[-1] += f' {word["text"]}'

        all_lines = list(filter(None, all_lines))  # Remove empty
        return os.linesep.join(all_lines)

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


class PSM(IntEnum):
    """Available tesseract mode options."""

    OSD_ONLY = 1  # Orientation and script detection (OSD) only.
    AUTO_OSD = 2  # Automatic page segmentation with orientation & script detection.
    AUTO_ONLY = 3  # Automatic page segmentation, but no OSD, or OCR.
    AUTO = 4  # Fully automatic page segmentation, but no OSD. (`tesserocr` default)
    SINGLE_COLUMN = 5  # Assume a single column of text of variable sizes.
    SINGLE_BLOCK_VERT_TEXT = 6  # Assume a  uniform block of vertically aligned text.
    SINGLE_BLOCK = 7  # Assume a single uniform block of text.
    SINGLE_LINE = 8  # Treat the image as a single text line.
    SINGLE_WORD = 9  # Treat the image as a single word.
    CIRCLE_WORD = 10  # Treat the image as a single word in a circle.
    SINGLE_CHAR = 11  # Treat the image as a single character.
    SPARSE_TEXT = 12  # Find as much text as possible in no particular order.
    SPARSE_TEXT_OSD = 13  # Sparse text with orientation and script det.
    RAW_LINE = 14  # Treat the image as a single text line, bypassing Tesseract hacks.
    COUNT = 15  # Number of enum entries.


class OEM(IntEnum):
    """Available tesseract model options."""

    TESSERACT_ONLY = 1  # Run Tesseract only - fastest
    LSTM_ONLY = 2  # Run just the LSTM line recognizer. (>=v4.00)
    TESSERACT_LSTM_COMBINED = 3  # Run the LSTM recognizer, but allow fallback
    # to Tesseract when things get difficult. (>=v4.00)
    CUBE_ONLY = 4  # Specify this mode when calling Init*(), to indicate that
    # any of the above modes should be automatically inferred from the
    # variables in the language-specific config, command-line configs, or
    # if not specified in any of the above should be set to the default
    # `OEM.TESSERACT_ONLY`.
    TESSERACT_CUBE_COMBINED = 5  # Run Cube only - better accuracy, but slower.
    DEFAULT = 6  # Run both and combine results - best accuracy.
