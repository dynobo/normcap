"""Various Data Models."""
import enum
import logging
from collections import namedtuple
from dataclasses import dataclass
from typing import Optional

from PySide6 import QtGui

logger = logging.getLogger(__name__)

Setting = namedtuple("Setting", "key flag type_ value choices help")


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
    xcb_error: str


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

    def __str__(self) -> str:
        return (
            f"(top={self.top}, left={self.left}, "
            f"bottom={self.bottom}, right={self.right})"
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


@dataclass
class Selection:
    """Represents selection on screen."""

    start_x: int = 0
    start_y: int = 0
    end_x: int = 0
    end_y: int = 0

    scale_factor: float = 1.0

    @property
    def rect(self) -> Rect:
        """Normalize position and return as Rect."""
        top = min(self.start_y, self.end_y)
        bottom = max(self.start_y, self.end_y)
        left = min(self.start_x, self.end_x)
        right = max(self.start_x, self.end_x)
        return Rect(top=top, left=left, bottom=bottom, right=right)

    @property
    def scaled_rect(self) -> Rect:
        """Resize rect by scale_factor."""
        rect = self.rect
        rect.top = int(rect.top * self.scale_factor)
        rect.bottom = int(rect.bottom * self.scale_factor)
        rect.left = int(rect.left * self.scale_factor)
        rect.right = int(rect.right * self.scale_factor)
        return rect


@dataclass()
class Screen:
    """About an attached display."""

    is_primary: bool
    device_pixel_ratio: float
    geometry: Rect
    index: int

    screenshot: Optional[QtGui.QImage] = None

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
    """Store all information like screenshot and selected region."""

    mode: CaptureMode = CaptureMode.PARSE

    # Image of selected region
    image: QtGui.QImage = QtGui.QImage()
    screen: Optional[Screen] = None
    scale_factor: float = 1
    rect: Rect = Rect()

    ocr_text: Optional[str] = None
    ocr_applied_magic: Optional[str] = None

    @property
    def image_area(self) -> int:
        """Provide area of cropped image in px²."""
        return self.rect.width * self.rect.height if self.image else 0
