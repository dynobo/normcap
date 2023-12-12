"""Various Data Models."""

import enum
import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Callable, NamedTuple, Optional, Union

from PySide6 import QtGui

logger = logging.getLogger(__name__)

# Type aliases
Seconds = float
Days = int


class Setting(NamedTuple):
    key: str
    flag: str
    type_: Union[type, Callable]
    value: Any
    choices: Optional[Iterable]
    help_: str
    cli_arg: bool
    nargs: Union[int, str, None]


@enum.unique
class DesktopEnvironment(enum.IntEnum):
    """Desktop environments that need to be handled."""

    OTHER = 0
    GNOME = 1
    KDE = 2
    SWAY = 3
    UNITY = 4
    HYPRLAND = 5


@enum.unique
class CaptureMode(enum.IntEnum):
    """Available modes of magic."""

    RAW = 0
    PARSE = 1


@dataclass
class Urls:
    """URLs used on various places."""

    releases: str
    changelog: str
    pypi: str
    github: str
    issues: str
    website: str
    faqs: str
    buymeacoffee: str

    @property
    def releases_atom(self) -> str:
        """URL to github releases rss feed."""
        return f"{self.releases}.atom"

    @property
    def pypi_json(self) -> str:
        """URL to github releases rss feed."""
        return f"{self.pypi}/json"


@dataclass()
class Rect:
    """Rectangular selection on screen.

    All points are inclusive (are part of the rectangle).
    """

    left: int
    top: int
    right: int
    bottom: int

    def __str__(self) -> str:
        return (
            f"(left={self.left}, top={self.top}, "
            f"right={self.right}, bottom={self.bottom})"
        )

    @property
    def geometry(self) -> tuple[int, int, int, int]:
        """Expose rect for usage with QT as (left, top, width, height)."""
        return self.left, self.top, self.width, self.height

    @property
    def coords(self) -> tuple[int, int, int, int]:
        """Expose rect as tuple of coordinates as (left, top, right, bottom)."""
        return self.left, self.top, self.right, self.bottom

    @property
    def width(self) -> int:
        """Width of rect."""
        return self.right - self.left + 1

    @property
    def height(self) -> int:
        """Height of rect."""
        return self.bottom - self.top + 1

    @property
    def size(self) -> tuple[int, int]:
        """Width and height of rect."""
        return (self.width, self.height)

    # ONHOLD: Annotate as Self with Python 3.11
    def scale(self, scale_factor: float):  # noqa: ANN201
        """Create an integer-scaled copy of the Rect."""
        return Rect(
            top=int(self.top * scale_factor),
            bottom=int(self.bottom * scale_factor),
            left=int(self.left * scale_factor),
            right=int(self.right * scale_factor),
        )


@dataclass()
class Screen(Rect):
    """Extends Rect with screen specific properties."""

    device_pixel_ratio: float
    index: int
    screenshot: Optional[QtGui.QImage] = None

    # ONHOLD: Annotate as Self with Python 3.11
    def scale(self, factor: Optional[float] = None):  # noqa: ANN201
        """Create an integer-scaled copy of the Rect."""
        factor = factor or 1 / self.device_pixel_ratio
        return Screen(
            device_pixel_ratio=1,
            index=self.index,
            screenshot=self.screenshot,
            top=int(self.top * factor),
            bottom=int(self.bottom * factor),
            left=int(self.left * factor),
            right=int(self.right * factor),
        )


@dataclass()
class Capture:
    """Store all information like screenshot and selected region."""

    mode: CaptureMode = CaptureMode.PARSE

    # Image of selected region
    image: QtGui.QImage = field(default_factory=QtGui.QImage)
    screen: Optional[Screen] = None
    scale_factor: float = 1
    rect: Rect = field(default_factory=lambda: Rect(left=0, top=0, right=0, bottom=0))

    ocr_text: Optional[str] = None
    ocr_magic: Optional[str] = None

    @property
    def image_area(self) -> int:
        """Provide area of cropped image in px²."""
        return self.rect.width * self.rect.height if self.image else 0
