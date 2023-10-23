import subprocess
import sys
from contextlib import contextmanager

import pytest

from normcap.clipboard.handlers import windll


@contextmanager
def clipboard_blocked():
    # Block Clipboard from being opened
    from ctypes import windll as c_windll  # type: ignore  # unknown on non-win32
    from ctypes.wintypes import BOOL, HWND

    OpenClipboard = c_windll.user32.OpenClipboard  # noqa: N806
    OpenClipboard.argtypes = [HWND]
    OpenClipboard.restype = BOOL

    safeCloseClipboard = c_windll.user32.CloseClipboard  # noqa: N806
    safeCloseClipboard.argtypes = []
    safeCloseClipboard.restype = BOOL

    try:
        assert OpenClipboard(0)
        yield
    finally:
        assert safeCloseClipboard()


@pytest.mark.parametrize(
    ("platform", "result"), [("win32", True), ("darwin", False), ("linux", False)]
)
def test_windll_is_compatible(monkeypatch, platform, result):
    monkeypatch.setattr(windll.sys, "platform", platform)
    assert windll.WindllHandler().is_compatible == result


@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_windll_copy():
    text = "test"
    result = windll.WindllHandler().copy(text=text)

    with subprocess.Popen(
        ["powershell", "-command", "Get-Clipboard"],  # noqa: S603, S607
        stdout=subprocess.PIPE,
    ) as p:
        stdout = p.communicate()[0]
    clipped = stdout.decode("utf-8").strip()

    assert result is True
    assert text == clipped


@pytest.mark.skipif(sys.platform == "win32", reason="Non-Windows specific test")
def test_windll_copy_on_non_win32():
    result = windll.WindllHandler().copy(text="this is a test")
    assert result is False


@pytest.mark.skipif(sys.platform == "win32", reason="non-Windows specific test")
def test_windll_copy_on_unsupported_platform_fails():
    result = windll.WindllHandler().copy(text="test")
    assert result is False


@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_windll_copy_with_blocked_clipboard_fails():
    with clipboard_blocked():
        result = windll.WindllHandler().copy(text="test")
    assert result is False
