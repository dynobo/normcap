"""Defines the data model for the whole program."""

# Default
import os
from dataclasses import dataclass, field

# Extra
from PIL import Image


@dataclass()
class NormcapData:
    """DataClass containing all session information of normcap.

    Including:
        - Images
        - Position information
        - OCR information
        - Runtime information
        - Additional meta data
    """

    image: Image = None  # Cropped image
    left: int = 0  # Position of cropped section
    right: int = 0
    top: int = 0
    bottom: int = 0
    monitor: int = 0  # Screen of cropped image
    line_boxes: list = field(default_factory=list)  # Detected OCR boxes
    shots: list = field(default_factory=list)  # Full images & position of all screens
    mode: str = ""  # Selected capture mode during crop
    cli_args: dict = field(default_factory=dict)  # normcap was called with those args

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
        return " ".join([l.content for l in self.line_boxes]).strip()

    @property
    def lines(self) -> str:
        """Helper to return concatenated OCR text in multiple lines.

        Returns:
            str -- stripped OCR lines concatenated using newline as separater
        """
        return os.linesep.join([l.content.strip() for l in self.line_boxes])
