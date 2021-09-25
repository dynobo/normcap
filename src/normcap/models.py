"""Various Data Models."""
import enum
import os
import statistics
from collections import namedtuple
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from PySide2 import QtGui

Setting = namedtuple("Setting", "key flag type_ value help")


@dataclass
class Urls:
    """URLs used on various places."""

    releases: str
    changelog: str
    pypi: str
    github: str
    issues: str
    faqs: str
    xcb_error: str


@enum.unique
class DisplayManager(enum.IntEnum):
    """Display manager that need to be handled."""

    OTHER = 0
    WAYLAND = 1
    X11 = 2


@enum.unique
class DesktopEnvironment(enum.IntEnum):
    """Desktop environments that need to be handled."""

    OTHER = 0
    GNOME = 1
    KDE = 2
    SWAY = 3


@enum.unique
class CaptureMode(enum.IntEnum):
    """Available modes of magic."""

    RAW = 0
    PARSE = 1


@dataclass()
class TesseractInfo:
    """Info about system's tesseract setup."""

    version: str
    path: str
    languages: List[str]


@dataclass()
class Rect:
    """Rectangular selection on screen."""

    left: int = 0
    top: int = 0
    right: int = 0
    bottom: int = 0

    @property
    def geometry(self) -> Tuple[int, int, int, int]:
        """Expose rect for usage with QT."""
        return self.left, self.top, self.width, self.height

    @property
    def points(self) -> Tuple[int, int, int, int]:
        """Expose rect as tuple of coordinates."""
        return self.left, self.top, self.right, self.bottom

    @property
    def width(self) -> int:
        """Width of rect."""
        return self.right - self.left

    @property
    def height(self) -> int:
        """Height of rect."""
        return self.bottom - self.top


@dataclass()
class ScreenInfo:
    """About an attached display."""

    is_primary: bool
    device_pixel_ratio: float
    geometry: Rect
    index: int

    @property
    def width(self):
        """Get screen width."""
        return self.geometry.width

    @property
    def height(self):
        """Get screen height."""
        return self.geometry.height


@dataclass()
class Capture:
    """Store all information about selected region."""

    mode: CaptureMode = CaptureMode.PARSE

    # Image of selected region
    image: QtGui.QImage = QtGui.QImage()
    screen: Optional[ScreenInfo] = None
    scale_factor: float = 1
    rect: Rect = Rect()

    # Result of OCR
    words: list = field(default_factory=list)  # Words+metadata detected by OCR

    # Result of magics
    scores: dict = field(default_factory=dict)  # magics with scores
    best_magic: str = ""  # Highest scored magic
    transformed: str = ""  # Transformed result

    # Technical information
    psm_opt: Optional[int] = None

    def __repr__(self) -> str:
        string = ""
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
        return string.strip()

    @staticmethod
    def _format_list_of_dicts_output(list_of_dicts: list) -> str:
        string = ""
        for dic in list_of_dicts:
            for key, val in dic.items():
                if key in ["left", "top", "width", "height"]:
                    string += f"{key}:{val: <5}| "
                elif key == "text":
                    string += f"{key}:{val}"
                else:
                    string += f"{key}:{val: <3}| "
            string += "\n"
        return string

    def _count_unique_sections(self, level: str) -> int:
        postfix = "_num"
        unique_sections = {w[level + postfix] for w in self.words}
        return len(unique_sections)

    @property
    def image_size(self):
        """Get image dimensions."""
        return self.image.size().toTuple()

    @property
    def mean_conf(self) -> float:
        """Average confidence value of OCR result."""
        if self.words:
            return statistics.mean([w.get("conf", 0) for w in self.words])
        return 0

    @property
    def text(self) -> str:
        """OCR text as single line string."""
        return " ".join(w["text"].strip() for w in self.words).strip()

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
                all_lines[-1] += " " + word["text"]

        all_lines = list(filter(None, all_lines))  # Remove empty
        return os.linesep.join(all_lines)

    @property
    def num_lines(self) -> int:
        """Number of lines in OCR text."""
        return self._count_unique_sections("line")

    @property
    def num_pars(self) -> int:
        """Number of paragraphs in OCR text."""
        return self._count_unique_sections("par")

    @property
    def num_blocks(self) -> int:
        """Number of text blocks in OCR text."""
        return self._count_unique_sections("block")

    @property
    def image_area(self) -> int:
        """Area of cropped image in px²."""
        return self.image_size[0] * self.image_size[1] if self.image else 0
