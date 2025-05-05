import subprocess
import sys

import pytest
from PySide6 import QtGui

from normcap.detection.ocr import tesseract


@pytest.mark.skipif(sys.platform == "win32", reason="Not implemented for Windows")
def test_run_command_raises_on_cmd_returned_error_code():
    cmd = ["bash", "-c", "'(exit 42);'"]
    with pytest.raises(subprocess.CalledProcessError) as e:
        _ = tesseract._run_command(cmd_args=cmd)
    assert e.value.cmd == cmd


def test_get_languages(tesseract_cmd, tessdata_path):
    langs = tesseract.get_languages(
        tesseract_cmd=tesseract_cmd, tessdata_path=tessdata_path
    )
    assert langs


def test_get_languages_on_windows(monkeypatch, tesseract_cmd, tessdata_path):
    def mocked_output(*_, **__):
        return subprocess.CompletedProcess(
            args="",
            returncode=0,
            stdout=(
                "List of available languages in "
                'C:\\Program Files\\Tesseract-OCR\\tessdata/" (2):\r\n'
                "\r\n"
                "ara\r\n"
                "eng\r\n"
            ),
        )

    monkeypatch.setattr(tesseract.subprocess, "run", mocked_output)
    langs = tesseract.get_languages(
        tesseract_cmd=tesseract_cmd, tessdata_path=tessdata_path
    )
    assert langs == ["ara", "eng"]


def test_get_languages_raise_on_wrong_cmd(tessdata_path):
    tesseract_cmd = "non-existing-binary"
    with pytest.raises(FileNotFoundError, match="Could not find Tesseract binary"):
        _ = tesseract.get_languages(
            tesseract_cmd=tesseract_cmd, tessdata_path=tessdata_path
        )


def test_get_languages_raise_on_no_languages(tmp_path, tesseract_cmd):
    tessdata_path = tmp_path
    with pytest.raises(ValueError, match="Could not load any languages"):
        _ = tesseract.get_languages(
            tesseract_cmd=tesseract_cmd, tessdata_path=tessdata_path
        )


def test_ocr_perform_raises_on_wrong_cmd():
    tesseract_cmd = "non-existing-binary"
    img = QtGui.QImage(200, 50, QtGui.QImage.Format.Format_RGB32)
    with pytest.raises(FileNotFoundError, match="Could not find Tesseract binary"):
        _ = tesseract.perform_ocr(
            tesseract_bin_path=tesseract_cmd, image=img, args=[""]
        )
