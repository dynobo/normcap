import logging
import os
import sys
from importlib import metadata, resources
from pathlib import Path

import pytest
from normcap import utils
from normcap.gui.models import Capture
from normcap.gui.settings import Settings
from normcap.ocr.models import OcrResult
from PIL import Image
from PySide6 import QtCore


def test_argparser_defaults_are_complete(argparser_defaults):
    args_keys = set(argparser_defaults.keys())
    expected_options = {
        "color",
        "language",
        "mode",
        "notification",
        "reset",
        "tray",
        "update",
        "verbosity",
        "version",
    }

    assert args_keys == expected_options


def test_argparser_help_is_complete():
    argparser = utils.create_argparser()
    assert len(argparser.description) > 10
    for action in argparser._actions:
        assert len(action.help) > 10


def test_argparser_attributes_in_settings(argparser_defaults):
    settings = Settings("normcap", "settings", init_settings={})

    for arg in argparser_defaults:
        if arg in ["verbosity", "reset"]:
            continue
        assert arg in settings.allKeys()


def test_settings_in_argparser_attributes(argparser_defaults):
    settings = Settings("normcap", "settings", init_settings={})
    for key in settings.allKeys():
        if key in ["version", "last-update-check"]:
            continue
        assert key in argparser_defaults


def test_argparser_defaults_are_correct(argparser_defaults):
    assert argparser_defaults.pop("reset") is False
    assert argparser_defaults.pop("version") is False
    assert argparser_defaults.pop("verbosity") == "warning"
    for value in argparser_defaults.values():
        assert value is None


@pytest.mark.parametrize("os_str", ("linux", "win32", "darwin"))
def test_set_environ_for_briefcase_not_packaged(monkeypatch, os_str):
    monkeypatch.setattr(utils.sys, "platform", os_str)

    tesseract_cmd = os.environ.get("TESSERACT_CMD", None)
    tesseract_version = os.environ.get("TESSERACT_VERSION", None)

    utils.set_environ_for_prebuild_package()

    assert tesseract_cmd == os.environ.get("TESSERACT_CMD", None)
    assert tesseract_version == os.environ.get("TESSERACT_VERSION", None)


@pytest.mark.parametrize("os_str", ("darwin", "linux", "win32"))
def test_set_environ_for_briefcase_is_packaged(monkeypatch, os_str):
    monkeypatch.setattr(metadata, "metadata", lambda _: ["Briefcase-Version"])
    monkeypatch.setattr(utils.sys, "platform", os_str)
    monkeypatch.setattr(utils.sys.modules["__main__"], "__package__", "normcap")

    monkeypatch.setenv("TESSERACT_CMD", "")
    monkeypatch.setenv("TESSERACT_VERSION", "")

    utils.set_environ_for_prebuild_package()

    if os_str == "win32":
        assert os.environ.get("TESSERACT_CMD").endswith("tesseract.exe")
        assert os.environ.get("TESSERACT_VERSION")
    else:
        assert os.environ.get("TESSERACT_CMD").endswith("tesseract")


def test_set_environ_for_briefcase_unsupported_platform(monkeypatch):
    monkeypatch.setattr(metadata, "metadata", lambda _: ["Briefcase-Version"])
    monkeypatch.setattr(utils.sys, "platform", "cygwin")
    monkeypatch.setattr(utils.sys.modules["__main__"], "__package__", "normcap")

    with pytest.raises(RuntimeError, match="Unsupported platform"):
        utils.set_environ_for_prebuild_package()


def test_init_tessdata_copies_files(tmp_path, monkeypatch):
    # Create placeholder for traineddata files, if they don't exist
    resource_path = Path(resources.files("normcap.resources"))
    traineddata_files = list((resource_path / "tessdata").glob("*.traineddata"))
    if not traineddata_files:
        (resource_path / "tessdata" / "placeholder_1.traineddata").touch()
        (resource_path / "tessdata" / "placeholder_2.traineddata").touch()

    try:
        monkeypatch.setattr(utils.system_info, "config_directory", lambda: tmp_path)
        tessdata_path = tmp_path / "tessdata"

        traineddatas = list(tessdata_path.glob("*.traineddata"))
        txts = list(tessdata_path.glob("*.txt"))
        assert not traineddatas
        assert not txts

        for _ in range(3):
            utils.copy_tessdata_files_to_config_dir()

            traineddatas = list(tessdata_path.glob("*.traineddata"))
            txts = list(tessdata_path.glob("*.txt"))
            assert traineddatas
            assert len(txts) == 1
    finally:
        # Make sure to delete possible placeholder files
        for f in (resource_path / "tessdata").glob("placeholder_?.traineddata"):
            f.unlink()


def test_qt_log_wrapper(qtlog, caplog):
    logger = logging.getLogger(__name__).root
    logger.setLevel("DEBUG")
    QtCore.qDebug("should_show_in_qtlog_only")
    QtCore.qInstallMessageHandler(utils.qt_log_wrapper)
    QtCore.qDebug("should_show_in_logger_only")

    qt_log_entries = [m.message.strip() for m in qtlog.records]
    assert len(qt_log_entries) == 1
    assert qt_log_entries[0] == "should_show_in_qtlog_only"

    assert "should_show_in_qtlog_only" not in caplog.text
    assert "should_show_in_logger_only" in caplog.text
    assert "[QT]" in caplog.text
    assert "debug" in caplog.text


def test_qt_log_wrapper_no_platform_as_error(caplog):
    logger = logging.getLogger(__name__).root
    logger.setLevel("DEBUG")
    QtCore.qInstallMessageHandler(utils.qt_log_wrapper)

    QtCore.qDebug("could not load the qt platform")

    assert "could not load the qt platform" in caplog.text
    assert "[qt]" in caplog.text.lower()
    assert "error" in caplog.text.lower()


def test_qt_log_wrapper_xcb_as_error(caplog):
    logger = logging.getLogger(__name__).root
    logger.setLevel("DEBUG")
    QtCore.qInstallMessageHandler(utils.qt_log_wrapper)

    QtCore.qDebug("xcb it was found")

    assert "[qt]" in caplog.text.lower()
    assert "xcb it was found" in caplog.text.lower()
    assert "try solving the problem" in caplog.text.lower()
    assert "error" in caplog.text.lower()


def test_hook_exception(monkeypatch, caplog, capsys):
    monkeypatch.setattr(sys, "exit", lambda _: True)
    with pytest.raises(RuntimeError) as excinfo:
        text = words = tsv_data = "secret"  # noqa: F841 (unused variable)
        transformed = v = self = "secret"  # noqa: F841
        other_variable = "should be printed"  # noqa: F841
        capture = Capture(ocr_text="secret")  # noqa: F841
        ocr_result = OcrResult(  # noqa: F841
            tess_args=None,
            image=Image.Image(),
            words="secret",
            transformed="secret",
        )
        raise RuntimeError

    utils.hook_exceptions(excinfo.type, excinfo.value, excinfo.tb)
    captured = capsys.readouterr()

    assert "Uncaught exception! Quitting NormCap!" in caplog.text
    assert "debug output limited" not in caplog.text

    assert "System:" in captured.err
    assert "Variables:" in captured.err
    assert "Traceback:" in captured.err
    assert "Exception:" in captured.err
    assert "RuntimeError" in captured.err

    assert "secret" not in captured.err
    assert "Capture(" in captured.err
    assert "OcrResult(" in captured.err
    assert "should be printed" in captured.err


def test_hook_exception_fails(monkeypatch, caplog):
    monkeypatch.setattr(sys, "exit", lambda _: True)
    with pytest.raises(RuntimeError) as excinfo:
        raise RuntimeError

    # Cause exception _inside_ the exception hook
    monkeypatch.setattr(utils.pprint, "pformat", lambda _: 1 / 0)
    utils.hook_exceptions(excinfo.type, excinfo.value, excinfo.tb)

    assert "Uncaught exception! Quitting NormCap!" in caplog.text
    assert "debug output limited" in caplog.text
