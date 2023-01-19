"""Various Data Models."""
from __future__ import annotations

import enum
import logging
from collections import namedtuple
from dataclasses import dataclass, field
from typing import Optional

from PySide6 import QtGui

logger = logging.getLogger(__name__)

Setting = namedtuple("Setting", "key flag type_ value choices help cli_arg nargs")


@enum.unique
class DesktopEnvironment(enum.IntEnum):
    """Desktop environments that need to be handled."""

    OTHER = 0
    GNOME = 1
    KDE = 2
    SWAY = 3
    UNITY = 4


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
    """Rectangular selection on screen."""

    left: int = 0
    top: int = 0
    right: int = 0
    bottom: int = 0

    def __str__(self) -> str:
        return (
            f"(left={self.left}, top={self.top}, "
            f"right={self.right}, bottom={self.bottom})"
        )

    @property
    def geometry(self) -> tuple[int, int, int, int]:
        """Expose rect for usage with QT."""
        return self.left, self.top, self.width, self.height

    @property
    def points(self) -> tuple[int, int, int, int]:
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

    @property
    def size(self) -> tuple[int, int]:
        """Width and height of rect."""
        return (self.width, self.height)

    def scaled(self, scale_factor: float) -> Rect:
        """Create an integer-scaled copy of the Rect."""
        return Rect(
            top=int(self.top * scale_factor),
            bottom=int(self.bottom * scale_factor),
            left=int(self.left * scale_factor),
            right=int(self.right * scale_factor),
        )


@dataclass()
class Screen:
    """About an attached display."""

    is_primary: bool
    device_pixel_ratio: float
    rect: Rect
    index: int

    screenshot: Optional[QtGui.QImage] = None

    @property
    def width(self) -> int:
        """Get screen width."""
        return self.rect.width

    @property
    def height(self) -> int:
        """Get screen height."""
        return self.rect.height


@dataclass()
class Capture:
    """Store all information like screenshot and selected region."""

    mode: CaptureMode = CaptureMode.PARSE

    # Image of selected region
    image: QtGui.QImage = field(default_factory=QtGui.QImage)
    screen: Optional[Screen] = None
    scale_factor: float = 1
    rect: Rect = field(default_factory=Rect)

    ocr_text: Optional[str] = None
    ocr_applied_magic: Optional[str] = None

    @property
    def image_area(self) -> int:
        """Provide area of cropped image in px²."""
        return self.rect.width * self.rect.height if self.image else 0
