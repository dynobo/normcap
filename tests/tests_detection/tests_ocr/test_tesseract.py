import logging
import subprocess
import sys

import pytest
from PySide6 import QtGui

from normcap.detection.ocr import tesseract
from normcap.gui import system_info


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
        _ = tesseract.perform_ocr(cmd=tesseract_cmd, image=img, args=[""])


@pytest.mark.parametrize(
    ("platform", "binary", "directory"),
    [
        ("linux", "tesseract", "bin"),
        ("win32", "tesseract.exe", "tesseract"),
        ("darwin", "tesseract", "bin"),
    ],
)
def test_get_tesseract_path_in_briefcase(monkeypatch, platform, binary, directory):
    with monkeypatch.context() as m:
        m.setattr(system_info, "is_briefcase_package", lambda: True)
        m.setattr(system_info.Path, "exists", lambda *args: True)
        m.setattr(system_info.sys, "platform", platform)
        path = tesseract.get_tesseract_path(
            is_briefcase_package=system_info.is_briefcase_package()
        )
    assert path.name == binary
    assert path.parent.name == directory


def test_get_tesseract_path_unknown_platform_raises(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(system_info, "is_briefcase_package", lambda: True)
        m.setattr(system_info.Path, "exists", lambda *args: True)
        m.setattr(system_info.sys, "platform", "unknown")
        with pytest.raises(ValueError, match="Platform unknown is not supported"):
            _ = tesseract.get_tesseract_path(
                is_briefcase_package=system_info.is_briefcase_package()
            )


def test_get_tesseract_path_missing_binary_raises(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(system_info, "is_briefcase_package", lambda: True)
        with pytest.raises(RuntimeError, match="Could not locate Tesseract binary"):
            _ = tesseract.get_tesseract_path(
                is_briefcase_package=system_info.is_briefcase_package()
            )


def test_get_tesseract_path_missing_tesseract_raises(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(tesseract.shutil, "which", lambda _: False)
        with pytest.raises(RuntimeError, match="No Tesseract binary found"):
            _ = tesseract.get_tesseract_path(
                is_briefcase_package=system_info.is_briefcase_package()
            )


@pytest.mark.parametrize(
    ("is_briefcase", "is_flatpak", "has_prefix", "expected_path_end"),
    [
        (True, False, False, "tessdata"),
        (False, True, False, "tessdata"),
        (False, False, True, "tessdata"),
        (False, False, False, None),
    ],
)
def test_get_tessdata_path(
    monkeypatch, caplog, is_briefcase, is_flatpak, has_prefix, expected_path_end
):
    data_file = system_info.config_directory() / "tessdata" / "mocked.traineddata"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.touch(exist_ok=True)

    try:
        with monkeypatch.context() as m:
            m.setattr(system_info, "is_briefcase_package", lambda: is_briefcase)
            m.setattr(system_info, "is_flatpak_package", lambda: is_flatpak)
            if has_prefix:
                m.setenv("TESSDATA_PREFIX", f"{data_file.resolve().parents[1]}")

            path_briefcase = tesseract.get_tessdata_path(
                config_directory=system_info.config_directory(),
                is_briefcase_package=is_briefcase,
                is_flatpak_package=is_flatpak,
            )

            path_end = (
                str(path_briefcase)[-len("tessdata") :] if path_briefcase else None
            )
            assert path_end == expected_path_end

    finally:
        data_file.unlink()


def test_get_tessdata_path_warn_on_win32(monkeypatch, caplog):
    data_file = system_info.config_directory() / "tessdata" / "mocked.traineddata"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.touch(exist_ok=True)

    try:
        with monkeypatch.context() as m:
            m.setattr(system_info, "is_briefcase_package", lambda: False)
            m.setattr(system_info, "is_flatpak_package", lambda: False)
            m.setenv("TESSDATA_PREFIX", "")

            monkeypatch.setattr(system_info.sys, "platform", "win32")
            with caplog.at_level(logging.WARNING):
                caplog.clear()
                _ = tesseract.get_tessdata_path(
                    config_directory=system_info.config_directory(),
                    is_briefcase_package=system_info.is_briefcase_package(),
                    is_flatpak_package=system_info.is_flatpak_package(),
                )
            assert "TESSDATA_PREFIX" in caplog.records[0].msg

    finally:
        data_file.unlink()
