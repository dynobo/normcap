"""Defines the data model for the whole program."""

# Default
import os
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

    # Set to true during unit tests only
    test_mode: bool = False

    # Result of start
    cli_args: dict = field(default_factory=dict)  # normcap was called with those args

    # Result of screenshot
    shots: list = field(default_factory=list)  # Full images & position of all screens

    # Results of cropping
    mode: str = ""  # Selected capture mode during crop ["raw","parsed"]
    image: Image = None  # Cropped image
    monitor: int = 0  # Screen of cropped image
    left: int = 0  # Position of cropped section
    right: int = 0
    top: int = 0
    bottom: int = 0

    # Result of OCR
    words: list = field(default_factory=list)  # Words+metadata detected by OCR

    # Result of ragics
    scores: dict = field(default_factory=dict)  # magics with scores
    best_magic: str = ""  # Highest scored magic
    transformed: str = ""  # Transformed result

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
        line_nums = set()
        for word in self.words:
            line_nums.add(word["line_num"])

        return len(line_nums)
