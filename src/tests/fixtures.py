"""Fixtures used by various tests."""

import pytest  # type: ignore
from PySide2 import QtGui

from normcap.models import (
    Capture,
    CaptureMode,
    Config,
    DesktopEnvironment,
    DisplayManager,
    Platform,
    Rect,
    ScreenInfo,
    SystemInfo,
)

# Allow pytest fixtures:
# pylint: disable=redefined-outer-name
# Allow usint privates:
# pylint: disable=protected-access


@pytest.fixture(scope="session")
def config() -> Config:
    """Create a config object."""
    return Config(
        color="#00ff00",
        language="eng",
        no_notifications=True,
        tray=False,
        verbose=True,
        very_verbose=True,
    )


@pytest.fixture(scope="session")
def capture() -> Capture:
    """Create argparser and provide its default values."""
    image = QtGui.QImage(200, 300, QtGui.QImage.Format.Format_RGB32)
    image.fill(QtGui.QColor("#ff0000"))
    # draw.rectangle((0, 0, 200, 160), fill=(0, 254, 0))

    return Capture(
        mode=CaptureMode.PARSE,
        rect=Rect(20, 30, 220, 330),
        transformed="",
        best_magic="",
        psm_opt=2,
        image=image,
        words=[
            {
                "level": 1,
                "page_num": 1,
                "block_num": 1,
                "par_num": 1,
                "line_num": 1,
                "word_num": 1,
                "left": 5,
                "top": 0,
                "width": 55,
                "height": 36,
                "conf": 20,
                "text": "one",
            },
            {
                "level": 1,
                "page_num": 1,
                "block_num": 1,
                "par_num": 2,
                "line_num": 1,
                "word_num": 2,
                "left": 5,
                "top": 0,
                "width": 55,
                "height": 36,
                "conf": 40,
                "text": "two",
            },
            {
                "level": 1,
                "page_num": 1,
                "block_num": 2,
                "par_num": 3,
                "line_num": 3,
                "word_num": 3,
                "left": 5,
                "top": 0,
                "width": 55,
                "height": 36,
                "conf": 30,
                "text": "three",
            },
        ],
    )


@pytest.fixture(scope="session")
def system_info() -> SystemInfo:
    """Create system info with two screens."""
    return SystemInfo(
        platform=Platform.LINUX,
        display_manager=DisplayManager.X11,
        desktop_environment=DesktopEnvironment.GNOME,
        normcap_version="version-string",
        tesseract_version="version-string",
        tessdata_path="./",
        tesseract_languages=["eng"],
        briefcase_package=False,
        screens={
            0: ScreenInfo(
                is_primary=False,
                index=0,
                device_pixel_ratio=1,
                geometry=Rect(),
            ),
            1: ScreenInfo(
                is_primary=True,
                index=1,
                device_pixel_ratio=1.5,
                geometry=Rect(),
            ),
        },
    )
