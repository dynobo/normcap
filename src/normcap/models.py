"""Various Data Models."""
import enum
import os
import pprint
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from PySide2 import QtGui

from normcap.logger import format_section


@dataclass
class Urls:
    """URLs used on various places."""

    releases = "https://github.com/dynobo/normcap/releases"
    pypi = "https://pypi.org/pypi/normcap"
    github = "https://github.com/dynobo/normcap"
    issues = "https://github.com/dynobo/normcap/issues"
    faqs = "https://github.com/dynobo/normcap/blob/main/FAQ.md"
    xcb_error = f"{faqs}#linux-could-not-load-the-qt-platform-plugin-xcb"


URLS = Urls()

FILE_ISSUE_TEXT = (
    "Please create a new issue with the output above on "
    f"{URLS.issues} . I'll see what I can do about it."
)


@enum.unique
class Platform(enum.IntEnum):
    """Support platform types."""

    LINUX = 1
    MACOS = 2
    WINDOWS = 3


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
class SystemInfo:
    "Information about the system."

    platform: Platform
    display_manager: DisplayManager
    desktop_environment: DesktopEnvironment
    normcap_version: str
    tesseract_version: str
    tesseract_languages: List[str]
    tessdata_path: str
    briefcase_package: bool
    screens: Dict[int, ScreenInfo] = field(default_factory=dict)

    @property
    def primary_screen_idx(self) -> int:
        """Get index from primary monitor."""
        for idx, screen in self.screens.items():
            if screen.is_primary:
                return idx
        raise ValueError("Unable to detect primary screen")

    def __repr__(self):
        string = pprint.pformat(self.__dict__, indent=3)
        string = format_section(string, "SystemInfo")
        return string


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
        """Format dataclass for debug outputs.

        Returns:
            str -- Representation of class
        """
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
        string = string.rstrip()
        string = format_section(string, "Capture")
        return string

    @property
    def image_size(self):
        """Get image dimensions."""
        return self.image.size

    @property
    def mean_conf(self) -> float:
        """Calculate mean confidence value of OCR.

        Returns:
            float -- Avg confidence value
        """
        if self.words:
            return statistics.mean([w.get("conf", 0) for w in self.words])
        return 0

    @property
    def text(self) -> str:
        """Concatenated OCR text into single line.

        Returns:
            str -- stripped OCR lines concatenated to single string
        """
        return " ".join([w["text"].strip() for w in self.words]).strip()

    @property
    def lines(self) -> str:
        """Concatenated OCR text into multiple lines.

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
        """Get number of lines.

        Returns:
            int -- number of detected lines
        """
        line_nums = {w["line_num"] for w in self.words}
        return len(line_nums)

    @property
    def num_pars(self) -> int:
        """Get number of paragraphs.

        Returns:
            int -- number of detected paragraphs
        """
        par_nums = {w["par_num"] for w in self.words}
        return len(par_nums)

    @property
    def num_blocks(self) -> int:
        """Get number of blocks.

        Returns:
            int -- number of detected blocks
        """
        par_blocks = {w["block_num"] for w in self.words}
        return len(par_blocks)

    @property
    def image_area(self) -> int:
        """Calculate area of cropped image in px².

        Returns:
            int -- Area of this.image in px²
        """
        if self.image is None:
            return 0

        return self.image.width() * self.image.height()

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
