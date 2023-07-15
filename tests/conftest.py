import sys
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from typing import Callable
from urllib import request

import pytest
from PySide6 import QtCore, QtGui, QtWidgets

from normcap import app
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

    except ImportError as e:
        raise RuntimeError(
            "Could not load DBUS! Consider skipping this test on this platform!"
        ) from e
    else:
        return dbus_portal


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


@pytest.fixture()
def basic_cli_args():
    """NormCap configuration used by most tests."""
    return [
        sys.argv[0],
        "--notification=False",
        "--verbosity=debug",
        "--update=False",
        "--tray=False",
    ]


@pytest.fixture()
def run_normcap(monkeypatch, qapp, basic_cli_args):
    def _run_normcap(extra_cli_args: list[str] | None = None):
        extra_cli_args = extra_cli_args or []
        basic_cli_args.extend(extra_cli_args)
        monkeypatch.setattr(sys, "argv", basic_cli_args)

        monkeypatch.setattr(app, "_get_application", lambda: qapp)
        _, tray = app._prepare()
        tray._EXIT_DELAY_MILLISECONDS = 100
        return tray

    return _run_normcap


@pytest.fixture()
def screen_size(qapp) -> QtCore.QSize:
    return QtWidgets.QApplication.instance()


@pytest.fixture()
def mock_urlopen(monkeypatch) -> Callable:
    """Provide a function to patch urllib.request.urlopen with a fake contextmanager.

    The fake urlopen contextmanager will yield a fake Response instance, which has
    only one `read()` method that returns the `response` data used as argument to patch
    function.

    If `response` is `None`, an exception is raised to simulate a download error.
    """

    class _MockedResponse:
        def __init__(self, response: bytes | None):
            self._response = response

        def read(self) -> bytes:
            if not self._response:
                raise RuntimeError("Simulate download failed")
            return self._response

    @contextmanager
    def _mocked_urlopen(*_, response: bytes | None, **__):
        yield _MockedResponse(response=response)

    def _monkeypatch_urlopen(response: bytes | None):
        monkeypatch.setattr(
            request, "urlopen", partial(_mocked_urlopen, response=response)
        )

    return _monkeypatch_urlopen


@pytest.fixture()
def select_region(qtbot):
    def _select_region(on: QtWidgets.QWidget, pos: tuple[QtCore.QPoint, QtCore.QPoint]):
        top_left, bottom_right = pos
        qtbot.mousePress(on, QtCore.Qt.MouseButton.LeftButton, pos=top_left)
        qtbot.mouseMove(on, pos=bottom_right)
        qtbot.mouseRelease(on, QtCore.Qt.MouseButton.LeftButton, pos=bottom_right)

    return _select_region
