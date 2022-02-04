"""Various Data Models."""
import enum
from collections import namedtuple
from dataclasses import dataclass
from typing import Optional

from PySide6 import QtCore, QtGui

Setting = namedtuple("Setting", "key flag type_ value help")


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

    def normalize(self):
        """Ensure that non-negative dimensions by flipping coordinates, if necessary."""
        if self.top > self.bottom:
            self.top, self.bottom = self.bottom, self.top
        if self.left > self.right:
            self.right, self.left = self.left, self.right

    def scale(self, factor: float):
        """Scale coordinates and dimensions by provided factor."""
        self.left = int(self.left * factor)
        self.top = int(self.top * factor)
        self.right = int(self.right * factor)
        self.bottom = int(self.bottom * factor)


@dataclass()
class Screen:
    """About an attached display."""

    is_primary: bool
    device_pixel_ratio: float
    geometry: Rect
    index: int

    raw_screenshot: Optional[QtGui.QImage] = None
    scaled_screenshot: Optional[QtGui.QImage] = None

    @property
    def width(self):
        """Get screen width."""
        return self.geometry.width

    @property
    def height(self):
        """Get screen height."""
        return self.geometry.height

    @property
    def screen_window_ratio(self):
        """Calculate ratio between raw and scaled screenshot.

        This is useful because the scaled screenshot (scaled to screen resolution) not
        necessary equals the size of the raw screenshot. This is the case e.g. if there
        are two differently scaled screeenshots (one HiDPI, one normal) or a monitor
        is set to fractional scaling.
        """
        return self.raw_screenshot.width() / self.scaled_screenshot.width()

    def get_scaled_screenshot(self, new_size: QtCore.QSize):
        """Resize screenshot to the provided dimensions and cache in attribute."""
        if not isinstance(self.raw_screenshot, QtGui.QImage):
            raise TypeError(
                f"Raw screenshot should be QImage but is {self.raw_screenshot}."
            )

        if (
            isinstance(self.scaled_screenshot, QtGui.QImage)
            and self.scaled_screenshot.size() == new_size
        ):
            return self.scaled_screenshot

        if new_size.width() == self.raw_screenshot.width():
            self.scaled_screenshot = self.raw_screenshot
        else:
            self.scaled_screenshot = self.raw_screenshot.scaled(
                new_size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
            )

        return self.scaled_screenshot


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
        return self.image.width() * self.image.height() if self.image else 0
