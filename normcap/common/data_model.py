"""Defines the data model for the whole program."""

# Default
import os
import sys
import statistics
from typing import Optional
from dataclasses import dataclass, field

# Extra
from PIL import Image  # type: ignore


@dataclass()
class NormcapData:
    """DataClass containing all session information of normcap.

    Including:
        - Images
        - Position information
        - OCR information
        - Runtime information
        - CLI arguments
        - Additional meta data
    """

    # Platform
    platform: str = sys.platform.lower()

    # Set to true during unit tests only
    test_mode: bool = False

    # Result of start
    cli_args: dict = field(default_factory=dict)  # normcap was called with those args

    # Result of screenshot
    shots: list = field(default_factory=list)  # Full images & position of all screens

    # Results of cropping
    mode: str = ""  # Selected capture mode during crop ["raw","parsed"]
    image: Optional[Image.Image] = None
    monitor: int = 0  # Screen of cropped image
    left: int = 0  # Position of cropped section
    right: int = 0
    top: int = 0
    bottom: int = 0

    # Result of OCR
    words: list = field(default_factory=list)  # Words+metadata detected by OCR

    # Result of magics
    scores: dict = field(default_factory=dict)  # magics with scores
    best_magic: str = ""  # Highest scored magic
    transformed: str = ""  # Transformed result

    def __repr__(self):
        """
        Returns:
            str -- Representation of class
        """
        string = f"\n{'='*20} <dataclass> {'='*20}\n"
        for key in dir(self):
            # Skip internal classes
            if key.startswith("_"):
                continue
            # Nicer format tesseract output
            if key == "words":
                string += f"{key}: \n{self._format_list_of_dicts_output(getattr(self, key))}\n"
                continue
            # Per default just print
            string += f"{key}: {getattr(self, key)}\n"
        string += f"{'='*20} </dataclass> {'='*19}"
        return string

    @property
    def mean_conf(self) -> float:
        """Helper to calculate mean confidence value of OCR.

        Returns:
            float -- Avg confidence value
        """
        if self.words:
            return statistics.mean([w.get("conf", 0) for w in self.words])
        else:
            return 0

    @property
    def selected_area(self) -> int:
        """Helper to calculate area of cropped image in px².

        Returns:
            int -- Area of this.image in px²
        """
        return int((self.bottom - self.top) * (self.right - self.left))

    @property
    def text(self) -> str:
        """Helper to return concatenated OCR text in single line.

        Returns:
            str -- stripped OCR lines concatenated to single string
        """
        return " ".join([w["text"].strip() for w in self.words]).strip()

    @property
    def lines(self) -> str:
        """Helper to return concatenated OCR text in multiple lines.

        Returns:
            str -- stripped OCR lines concatenated using newline as separater
        """
        current_line_num = 0
        all_lines = []
        for word in self.words:
            if word["line_num"] != current_line_num:
                current_line_num = word["line_num"]
                all_lines.append(word["text"])
            else:
                all_lines[-1] += " " + word["text"]

        all_lines = list(filter(None, all_lines))  # Remove empty
        return os.linesep.join(all_lines)

    @property
    def num_lines(self) -> int:
        """Helper to return number of lines.

        Returns:
            int -- number of detected lines
        """
        line_nums = set([w["line_num"] for w in self.words])
        return len(line_nums)

    @property
    def num_pars(self) -> int:
        """Helper to return number of paragraphs.

        Returns:
            int -- number of detected paragraphs
        """
        par_nums = set([w["par_num"] for w in self.words])
        return len(par_nums)

    @property
    def num_blocks(self) -> int:
        """Helper to return number of blocks.

        Returns:
            int -- number of detected blocks
        """
        par_blocks = set([w["block_num"] for w in self.words])
        return len(par_blocks)

    def _format_list_of_dicts_output(self, list_of_dicts: list) -> str:
        string = ""
        for d in list_of_dicts:
            for key, val in d.items():
                if key in ["left", "top", "width", "height"]:
                    string += f"{key}:{val: <5}| "
                elif key == "text":
                    string += f"{key}:{val}"
                else:
                    string += f"{key}:{val: <3}| "
            string += "\n"
        return string
