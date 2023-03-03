import subprocess
import sys

import pytest

from normcap import clipboard


def test_get_copy_func_with_pbcopy(monkeypatch):
    monkeypatch.setattr(clipboard.macos.shutil, "which", lambda *args: True)
    get_copy = clipboard.macos.get_copy_func()
    assert get_copy == clipboard.macos.pbcopy


def test_get_copy_func_without_pbcopy(monkeypatch):
    monkeypatch.setattr(clipboard.macos.shutil, "which", lambda *args: None)
    get_copy = clipboard.macos.get_copy_func()
    assert get_copy == clipboard.qt.copy


def test_perform_pbcopy():
    if sys.platform != "darwin":
        pytest.xfail("not macOS")

    text = "my test string"
    clipboard.macos.pbcopy(text)
    with subprocess.Popen(
        ["pbpaste", "r"], stdout=subprocess.PIPE, close_fds=True
    ) as p:
        stdout = p.communicate()[0]
    clipped = stdout.decode("utf-8")
    assert text == clipped
