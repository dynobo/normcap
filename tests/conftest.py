import sys
from pathlib import Path

import pytest
from PySide6 import QtCore, QtGui

from normcap.gui import menu_button, system_info
from normcap.gui.models import Capture, CaptureMode, Rect
from normcap.ocr.magics import email_magic, url_magic
from normcap.ocr.models import OEM, PSM, OcrResult, TessArgs
from normcap.screengrab import utils as screengrab_utils
from normcap.utils import create_argparser


@pytest.fixture(autouse=True)
def _clear_caches():
    screengrab_utils.get_gnome_version.cache_clear()
    url_magic.UrlMagic._extract_urls.cache_clear()
    email_magic.EmailMagic._extract_emails.cache_clear()
    system_info.desktop_environment.cache_clear()
    system_info.display_manager_is_wayland.cache_clear()
    system_info.get_tesseract_path.cache_clear()
    system_info.config_directory.cache_clear()


@pytest.fixture()
def temp_settings():
    settings = QtCore.QSettings("dynobo", "normcap_tests")
    yield settings
    settings.remove("")


@pytest.fixture()
def menu_btn(temp_settings):
    return menu_button.MenuButton(
        settings=temp_settings, language_manager=True, installed_languages=["eng"]
    )


@pytest.fixture()
def menu_btn_without_lang_man(temp_settings):
    return menu_button.MenuButton(
        settings=temp_settings, language_manager=False, installed_languages=["eng"]
    )


@pytest.fixture()
def dbus_portal(qapp):
    try:
        from normcap.screengrab import dbus_portal

        return dbus_portal
    except ImportError as e:
        if sys.platform != "linux":
            pytest.xfail(f"Import error: {e}")


@pytest.fixture()
def capture() -> Capture:
    """Create argparser and provide its default values."""
    image = QtGui.QImage(200, 300, QtGui.QImage.Format.Format_RGB32)
    image.fill(QtGui.QColor("#ff0000"))

    return Capture(
        mode=CaptureMode.PARSE,
        rect=Rect(20, 30, 220, 330),
        ocr_text="one two three",
        ocr_applied_magic="",
        image=image,
    )


@pytest.fixture()
def ocr_result() -> OcrResult:
    """Create argparser and provide its default values."""
    return OcrResult(
        tess_args=TessArgs(
            tessdata_path=Path(),
            lang="eng",
            oem=OEM.TESSERACT_LSTM_COMBINED,
            psm=PSM.AUTO_ONLY,
        ),
        image=QtGui.QImage(),
        magic_scores={},
        parsed="",
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


@pytest.fixture()
def argparser_defaults():
    argparser = create_argparser()
    return vars(argparser.parse_args([]))
