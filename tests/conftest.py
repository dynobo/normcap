import builtins
import importlib
import sys
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from types import ModuleType
from typing import Callable, Optional
from urllib import request

import pytest
from PySide6 import QtCore, QtGui, QtWidgets

from normcap import app
from normcap.clipboard import system_info as clipboard_system_info
from normcap.gui import menu_button, system_info
from normcap.gui.models import Capture, CaptureMode, Rect
from normcap.ocr.structures import OEM, PSM, OcrResult, TessArgs
from normcap.ocr.transformers import email, url
from normcap.screengrab import system_info as screengrab_system_info


@pytest.fixture(autouse=True)
def _clear_caches():
    screengrab_system_info.get_gnome_version.cache_clear()
    clipboard_system_info.get_gnome_version.cache_clear()
    url._extract_urls.cache_clear()
    email._extract_emails.cache_clear()
    system_info.desktop_environment.cache_clear()
    system_info.display_manager_is_wayland.cache_clear()
    system_info.get_tesseract_path.cache_clear()
    system_info.config_directory.cache_clear()


@pytest.fixture()
def temp_settings(qapp):
    settings = QtCore.QSettings("normcap_tests", "settings")
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
        from normcap.screengrab.handlers import dbus_portal

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
        ocr_transformer=None,
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
            psm=PSM.AUTO,
        ),
        image=QtGui.QImage(),
        transformer_scores={},
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
def basic_cli_args():
    """NormCap configuration used by most tests."""
    return [
        sys.argv[0],
        "--mode=parse",
        "--notification=False",
        "--verbosity=debug",
        "--update=False",
        "--tray=False",
        "--show-introduction=False",
    ]


@pytest.fixture()
def run_normcap(monkeypatch, qapp, qtbot, basic_cli_args):
    trays = []

    def _run_normcap(extra_cli_args: Optional[list[str]] = None):
        extra_cli_args = extra_cli_args or []
        basic_cli_args.extend(extra_cli_args)
        monkeypatch.setattr(sys, "argv", basic_cli_args)

        monkeypatch.setattr(app, "_get_application", lambda: qapp)
        _, tray = app._prepare()

        # wait for windows to be created and moved on wayland
        qtbot.wait(50)

        tray._EXIT_DELAY = 0.1
        trays.append(tray)
        return tray

    yield _run_normcap

    for tray in trays:
        tray._close_windows()
        tray._exit_application(delay=0)
        tray.deleteLater()

    QtCore.QTimer.singleShot(0, QtCore.QCoreApplication.processEvents)


@pytest.fixture()
def test_signal():
    """Create a QT signal for usage with qtbot.waitSignal().

    In many situation it's necessary to let the QT process until a certain condition is
    met. The of pytest-qt for such a use-case is to use `qtbot.waitUntil(<condition>)`.

    Unfortunately, qtbot.waitUntil() is (sometimes?) unreliable on macOS and may lead
    to indefinite hangs. In such a case `qtbot.waitSignal(test_signal.on_event)` can be
    used in conjunction with monkeypatching `test_signal.on_event.emit(<data>)` at the
    desired call.

    See e.g. /test/integration/test_normcap.py for an application.
    """

    class TestSignal(QtCore.QObject):
        on_event = QtCore.Signal(int)

    return TestSignal()


@pytest.fixture()
def mock_urlopen(monkeypatch) -> Callable:
    """Provide a function to patch urllib.request.urlopen with a fake contextmanager.

    The fake urlopen contextmanager will yield a fake Response instance, which has
    only one `read()` method that returns the `response` data used as argument to patch
    function.

    If `response` is `None`, an exception is raised to simulate a download error.
    """

    class _MockedResponse:
        def __init__(self, response: Optional[bytes]):
            self._response = response

        def read(self) -> bytes:
            if not self._response:
                raise RuntimeError("Simulate download failed")
            return self._response

    @contextmanager
    def _mocked_urlopen(*_, response: Optional[bytes], **__):
        yield _MockedResponse(response=response)

    def _monkeypatch_urlopen(response: Optional[bytes]):
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
        qtbot.wait(500)

    return _select_region


@pytest.fixture()
def mock_import(monkeypatch):
    def _mock_import(
        parent_module: ModuleType,
        import_name: str,
        throw_exc: type[Exception],
    ):
        real_import = builtins.__import__

        def _mocked_import(
            name,
            globals=None,  # noqa: A002  # intentional
            locals=None,  # noqa: A002 # intentional
            fromlist=(),
            level=0,
        ):
            if name == import_name or fromlist and import_name in fromlist:
                raise throw_exc(f"Mocked import error {import_name}")
            return real_import(
                name, globals=globals, locals=locals, fromlist=fromlist, level=level
            )

        monkeypatch.delattr(parent_module, import_name, raising=False)
        monkeypatch.setattr(builtins, "__import__", _mocked_import)
        importlib.reload(parent_module)

    return _mock_import
