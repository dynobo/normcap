"""Mainly taken from PyperClip, https://github.com/asweigart/pyperclip.

Heavily stripped down version of the windows related functionality, slightly modified.

A cross-platform clipboard module for Python, with copy & paste functions for plain
text.
By Al Sweigart al@inventwithpython.com
BSD License
"""

import contextlib
import ctypes
import logging
import sys
import time
from collections.abc import Generator, Iterator
from ctypes import c_size_t, c_wchar, c_wchar_p, get_errno, sizeof
from typing import Any

logger = logging.getLogger(__name__)

install_instructions = ""  #  msvcrt is pre-installed on Windows


class CheckedCall:
    def __init__(self, f: Any) -> None:  # noqa: ANN401
        self.argtypes: list
        self.restype: Any
        self.f: Any
        super().__setattr__("f", f)

    def __call__(self, *args: Any) -> Any:  # noqa: ANN401
        ret = self.f(*args)
        if not ret and get_errno():
            raise RuntimeError(f"Error calling {self.f.__name__}")  # pragma: no cover
        return ret

    def __setattr__(self, key: str, value: Any) -> None:  # noqa: ANN401, D105
        setattr(self.f, key, value)


# TODO: Think about pulling ctype imports and context managers out
def copy(text: str) -> None:  # noqa: PLR0915
    from ctypes.wintypes import (
        BOOL,
        DWORD,
        HANDLE,
        HGLOBAL,
        HINSTANCE,
        HMENU,
        HWND,
        INT,
        LPCSTR,
        LPVOID,
        UINT,
    )

    windll = ctypes.windll  # type:ignore  # not available on non-Windows systems
    msvcrt = ctypes.CDLL("msvcrt")

    safeCreateWindowExA = CheckedCall(windll.user32.CreateWindowExA)  # noqa: N806
    safeCreateWindowExA.argtypes = [
        DWORD,
        LPCSTR,
        LPCSTR,
        DWORD,
        INT,
        INT,
        INT,
        INT,
        HWND,
        HMENU,
        HINSTANCE,
        LPVOID,
    ]
    safeCreateWindowExA.restype = HWND

    safeDestroyWindow = CheckedCall(windll.user32.DestroyWindow)  # noqa: N806
    safeDestroyWindow.argtypes = [HWND]
    safeDestroyWindow.restype = BOOL

    OpenClipboard = windll.user32.OpenClipboard  # noqa: N806
    OpenClipboard.argtypes = [HWND]
    OpenClipboard.restype = BOOL

    safeCloseClipboard = CheckedCall(windll.user32.CloseClipboard)  # noqa: N806
    safeCloseClipboard.argtypes = []
    safeCloseClipboard.restype = BOOL

    safeEmptyClipboard = CheckedCall(windll.user32.EmptyClipboard)  # noqa: N806
    safeEmptyClipboard.argtypes = []
    safeEmptyClipboard.restype = BOOL

    safeGetClipboardData = CheckedCall(windll.user32.GetClipboardData)  # noqa: N806
    safeGetClipboardData.argtypes = [UINT]
    safeGetClipboardData.restype = HANDLE

    safeSetClipboardData = CheckedCall(windll.user32.SetClipboardData)  # noqa: N806
    safeSetClipboardData.argtypes = [UINT, HANDLE]
    safeSetClipboardData.restype = HANDLE

    safeGlobalAlloc = CheckedCall(windll.kernel32.GlobalAlloc)  # noqa: N806
    safeGlobalAlloc.argtypes = [UINT, c_size_t]
    safeGlobalAlloc.restype = HGLOBAL

    safeGlobalLock = CheckedCall(windll.kernel32.GlobalLock)  # noqa: N806
    safeGlobalLock.argtypes = [HGLOBAL]
    safeGlobalLock.restype = LPVOID

    safeGlobalUnlock = CheckedCall(windll.kernel32.GlobalUnlock)  # noqa: N806
    safeGlobalUnlock.argtypes = [HGLOBAL]
    safeGlobalUnlock.restype = BOOL

    wcslen = CheckedCall(msvcrt.wcslen)
    wcslen.argtypes = [c_wchar_p]
    wcslen.restype = UINT

    GMEM_MOVEABLE = 0x0002  # noqa: N806 (lowercase)
    CF_UNICODETEXT = 13  # noqa: N806 (lowercase)

    @contextlib.contextmanager
    def window() -> Iterator[HWND]:
        """Context that provides a valid Windows hwnd."""
        # we really just need the hwnd, so setting "STATIC"
        # as predefined lpClass is just fine.
        hwnd = safeCreateWindowExA(
            0, b"STATIC", None, 0, 0, 0, 0, 0, None, None, None, None
        )
        try:
            yield hwnd
        finally:
            safeDestroyWindow(hwnd)

    @contextlib.contextmanager
    def clipboard(hwnd: HWND) -> Generator:
        """Open the clipboard and prevents other apps from modifying its content."""
        # We may not get the clipboard handle immediately because
        # some other application is accessing it (?)
        # We try for at least 500ms to get the clipboard.
        t = time.time() + 0.5
        success = False
        while time.time() < t:
            success = OpenClipboard(hwnd)
            if success:
                break
            time.sleep(0.01)
        if not success:
            raise RuntimeError("Error calling OpenClipboard")

        try:
            yield
        finally:
            safeCloseClipboard()

    def copy_windows(text: str) -> None:
        with window() as hwnd, clipboard(hwnd):
            # http://msdn.com/ms649048
            # If an application calls OpenClipboard with hwnd set to NULL,
            # EmptyClipboard sets the clipboard owner to NULL;
            # this causes SetClipboardData to fail.
            # => We need a valid hwnd to copy something.
            safeEmptyClipboard()

            if text:
                # http://msdn.com/ms649051
                # If the hMem parameter identifies a memory object,
                # the object must have been allocated using the
                # function with the GMEM_MOVEABLE flag.
                count = wcslen(text) + 1
                handle = safeGlobalAlloc(GMEM_MOVEABLE, count * sizeof(c_wchar))
                locked_handle = safeGlobalLock(handle)

                ctypes.memmove(
                    c_wchar_p(locked_handle),
                    c_wchar_p(text),
                    count * sizeof(c_wchar),
                )

                safeGlobalUnlock(handle)
                safeSetClipboardData(CF_UNICODETEXT, handle)

    copy_windows(text)


def is_compatible() -> bool:
    if sys.platform != "win32":
        logger.debug("%s is incompatible on non-Windows systems", __name__)
        return False

    logger.debug("%s is compatible", __name__)
    return True


def is_installed() -> bool:
    logger.debug("%s requires no dependencies", __name__)
    return True
