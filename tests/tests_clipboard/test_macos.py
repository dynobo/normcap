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


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS specific test")
def test_perform_pbcopy():
    text = "my test string"
    clipboard.macos.pbcopy(text)
    with subprocess.Popen(
        ["pbpaste", "r"], stdout=subprocess.PIPE  # noqa: S603, S607
    ) as p:
        stdout = p.communicate()[0]
    clipped = stdout.decode("utf-8")
    assert text == clipped
