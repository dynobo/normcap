import logging
import os
import sys
from importlib import resources
from pathlib import Path

import pytest
from PySide6 import QtCore, QtGui

from normcap import utils
from normcap.gui import system_info
from normcap.gui.models import Capture
from normcap.gui.settings import Settings
from normcap.ocr.models import OEM, PSM, OcrResult, TessArgs


def test_argparser_defaults_are_complete():
    # GIVEN the argparser parses empty cli args
    parser = utils.create_argparser()

    # WHEN it parses an empty list of args
    parsed_args = parser.parse_args([])

    # THEN an expected set of options should be present with default values
    expected_options = {
        "background_mode",
        "color",
        "cli_mode",
        "language",
        "mode",
        "notification",
        "reset",
        "tray",
        "update",
        "verbosity",
        "version",
    }
    args_keys = set(vars(parsed_args).keys())
    assert args_keys == expected_options


def test_argparser_help_is_complete():
    # WHEN instantiating the argparser
    argparser = utils.create_argparser()

    # THEN it should contain a description
    #    and all actions should have a help text
    assert argparser.description
    assert len(argparser.description) > 10

    for action in argparser._actions:
        assert action.help
        assert len(action.help) > 10


def test_argparser_parses_all_types(monkeypatch):
    # GIVEN an argparser
    argparser = utils.create_argparser()

    # WHEN parsing a list of args with string representing various types
    monkeypatch.setattr(
        sys,
        "argv",
        """python
           --notification True
           --tray 0
           --verbosity info
           --language uvw xyz
        """.split(),
    )
    args = argparser.parse_args()

    # THEN the various types should be parsed into the correct types
    assert args.notification is True
    assert args.tray is False
    assert args.verbosity == "info"
    assert args.language == ["uvw", "xyz"]


def test_argparser_attributes_in_settings():
    argparser_defaults = vars(utils.create_argparser().parse_args([]))
    settings = Settings(organization="normcap_TEST")

    for arg in argparser_defaults:
        if arg in (
            "verbosity",
            "reset",
            "cli_mode",
            "background_mode",
        ):
            continue
        assert arg in settings.allKeys()


def test_settings_in_argparser_attributes():
    argparser_defaults = vars(utils.create_argparser().parse_args([]))
    settings = Settings(organization="normcap_TEST")
    for key in settings.allKeys():
        if key in ("version", "last-update-check"):
            continue
        assert key in argparser_defaults


def test_argparser_defaults_are_correct():
    argparser_defaults = vars(utils.create_argparser().parse_args([]))
    assert argparser_defaults.pop("reset") is False
    assert argparser_defaults.pop("version") is False
    assert argparser_defaults.pop("cli_mode") is False
    assert argparser_defaults.pop("background_mode") is False
    assert argparser_defaults.pop("verbosity") == "warning"
    for value in argparser_defaults.values():
        assert value is None


def test_set_environ_for_wayland(monkeypatch):
    xcursor_size = os.environ.get("XCURSOR_SIZE", "")
    qt_qpa_platform = os.environ.get("QT_QPA_PLATFORM", "")

    try:
        with monkeypatch.context() as m:
            m.delenv("XCURSOR_SIZE", raising=False)
            m.delenv("QT_QPA_PLATFORM", raising=False)

            utils.set_environ_for_wayland()

            assert os.environ.get("XCURSOR_SIZE") == "24"
            assert os.environ.get("QT_QPA_PLATFORM") == "wayland"
    finally:
        os.environ["XCURSOR_SIZE"] = xcursor_size
        os.environ["QT_QPA_PLATFORM"] = qt_qpa_platform


def test_set_environ_for_wayland_use_wlcopy(monkeypatch):
    path = os.environ.get("PATH", "")
    try:
        with monkeypatch.context() as m:
            m.setattr(utils.system_info, "is_briefcase_package", lambda: True)
            m.setattr(utils.shutil, "which", lambda *args: False)
            m.delenv("PATH", raising=False)
            utils.set_environ_for_wayland()
            new_path = os.environ.get("PATH", "")
            assert new_path.endswith(f"{os.sep}bin{os.pathsep}")
    finally:
        os.environ["PATH"] = path


def test_set_environ_for_flatpak(monkeypatch):
    with monkeypatch.context() as m:
        test_value = "something"
        m.setenv("LD_PRELOAD", test_value)
        utils.set_environ_for_flatpak()
        assert os.environ.get("LD_PRELOAD") == test_value

        m.setenv("LD_PRELOAD", "nocsd")
        utils.set_environ_for_flatpak()
        assert not os.environ.get("LD_PRELOAD")

        m.delenv("LD_PRELOAD", raising=False)
        utils.set_environ_for_flatpak()
        assert os.environ.get("LD_PRELOAD", None) is None


def test_copy_traineddata_files_briefcase(tmp_path, monkeypatch):
    # Create placeholder for traineddata files, if they don't exist
    monkeypatch.setattr(system_info, "is_briefcase_package", lambda: True)
    with resources.as_file(resources.files("normcap.resources")) as file_path:
        resource_path = Path(file_path)
    (resource_path / "tessdata" / "placeholder_1.traineddata").touch()
    (resource_path / "tessdata" / "placeholder_2.traineddata").touch()

    try:
        tessdata_path = tmp_path / "tessdata"
        traineddatas = list(tessdata_path.glob("*.traineddata"))
        txts = list(tessdata_path.glob("*.txt"))
        assert not traineddatas
        assert not txts

        # Copying without should copy the temporary traineddata files
        for _ in range(3):
            utils.copy_traineddata_files(target_dir=tessdata_path)

            traineddatas = list(tessdata_path.glob("*.traineddata"))
            txts = list(tessdata_path.glob("*.txt"))
            assert traineddatas
            assert len(txts) == 2

    finally:
        # Make sure to delete possible placeholder files
        for f in (resource_path / "tessdata").glob("placeholder_?.traineddata"):
            f.unlink()


def test_copy_traineddata_files_flatpak(tmp_path, monkeypatch):
    # Create placeholder for traineddata files, if they don't exist
    monkeypatch.setattr(utils.system_info, "is_flatpak_package", lambda: True)
    with resources.as_file(resources.files("normcap.resources")) as file_path:
        resource_path = Path(file_path)
    (resource_path / "tessdata" / "placeholder_1.traineddata").touch()
    (resource_path / "tessdata" / "placeholder_2.traineddata").touch()
    try:
        tessdata_path = tmp_path / "tessdata"
        traineddatas = list(tessdata_path.glob("*.traineddata"))
        txts = list(tessdata_path.glob("*.txt"))
        assert not traineddatas
        assert not txts

        paths = []

        def mocked_path(path_str: str):
            paths.append(path_str)
            if path_str == "/app/share/tessdata":
                path_str = str(resource_path / "tessdata")
            return Path(path_str)

        monkeypatch.setattr(utils, "Path", mocked_path)
        for _ in range(3):
            utils.copy_traineddata_files(target_dir=tessdata_path)

            traineddatas = list(tessdata_path.glob("*.traineddata"))
            txts = list(tessdata_path.glob("*.txt"))
            assert traineddatas
            assert len(txts) == 2
            assert "/app/share/tessdata" in paths
    finally:
        # Make sure to delete possible placeholder files
        for f in (resource_path / "tessdata").glob("placeholder_?.traineddata"):
            f.unlink()


def test_copy_traineddata_files_not_copying(tmp_path, monkeypatch):
    # Create placeholder for traineddata files, if they don't exist
    with resources.as_file(resources.files("normcap.resources")) as file_path:
        resource_path = Path(file_path)
    (resource_path / "tessdata" / "placeholder_1.traineddata").touch()
    (resource_path / "tessdata" / "placeholder_2.traineddata").touch()

    try:
        tessdata_path = tmp_path / "tessdata"

        # Copying without being flatpak or briefcase should do nothing
        utils.copy_traineddata_files(target_dir=tessdata_path)

        traineddatas = list(tessdata_path.glob("*.traineddata"))
        txts = list(tessdata_path.glob("*.txt"))
        assert not traineddatas
        assert not txts

        # Copying within package but with target_path=None should do nothing
        monkeypatch.setattr(system_info, "is_briefcase_package", lambda: True)
        utils.copy_traineddata_files(target_dir=None)

        traineddatas = list(tessdata_path.glob("*.traineddata"))
        txts = list(tessdata_path.glob("*.txt"))
        assert not traineddatas
        assert not txts
    finally:
        # Make sure to delete possible placeholder files
        for f in (resource_path / "tessdata").glob("placeholder_?.traineddata"):
            f.unlink()


def test_qt_log_wrapper(qtlog, caplog):
    logger = logging.getLogger(__name__).root
    logger.setLevel("DEBUG")
    QtCore.qDebug("should_show_in_qtlog_only")  # type: ignore # Wrong in PySide?

    QtCore.qInstallMessageHandler(utils.qt_log_wrapper)
    QtCore.qDebug("should_show_in_logger_only")  # type: ignore # Wrong in PySide?

    qt_log_entries = [m.message.strip() for m in qtlog.records]
    assert len(qt_log_entries) == 1
    assert qt_log_entries[0] == "should_show_in_qtlog_only"

    assert "should_show_in_qtlog_only" not in caplog.text
    assert "should_show_in_logger_only" in caplog.text
    assert "[QT]" in caplog.text
    assert "debug" in caplog.text


def test_qt_log_wrapper_silence_opentype_warning(caplog):
    logger = logging.getLogger(__name__).root
    logger.setLevel("DEBUG")
    QtCore.qInstallMessageHandler(utils.qt_log_wrapper)

    QtCore.qDebug("Warning, OpenType support missing for OpenSans")  # type: ignore

    assert "[qt]" not in caplog.text.lower()
    assert "error" not in caplog.text.lower()


def test_qt_log_wrapper_no_platform_as_error(caplog):
    logger = logging.getLogger(__name__).root
    logger.setLevel("DEBUG")
    QtCore.qInstallMessageHandler(utils.qt_log_wrapper)

    QtCore.qDebug("could not load the qt platform")  # type: ignore # Wrong in PySide?

    assert "could not load the qt platform" in caplog.text
    assert "[qt]" in caplog.text.lower()
    assert "error" in caplog.text.lower()


def test_qt_log_wrapper_xcb_as_error(caplog):
    logger = logging.getLogger(__name__).root
    logger.setLevel("DEBUG")
    QtCore.qInstallMessageHandler(utils.qt_log_wrapper)

    QtCore.qDebug("xcb it was found")  # type: ignore # Wrong in PySide?

    assert "[qt]" in caplog.text.lower()
    assert "xcb it was found" in caplog.text.lower()
    assert "installing additional dep" in caplog.text.lower()
    assert "error" in caplog.text.lower()


def test_hook_exception(monkeypatch, caplog, capsys):
    with monkeypatch.context() as m:
        m.setattr(sys, "exit", lambda _: True)

        def raise_exception():
            text = words = tsv_data = "secret"  # noqa: F841 (unused variable)
            transformed = v = self = "secret"  # noqa: F841
            other_variable = "should be printed"  # noqa: F841
            capture = Capture(ocr_text="secret")  # noqa: F841
            ocr_result = OcrResult(  # noqa: F841
                tess_args=TessArgs(Path.cwd(), "eng", OEM.DEFAULT, PSM.AUTO),
                image=QtGui.QImage(),
                words=[{"secret": "value"}],
                parsed="secret",
            )
            raise RuntimeError

        with pytest.raises(RuntimeError) as exc:
            raise_exception()

        utils.hook_exceptions(exc.type, exc.value, exc.tb)

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
    with monkeypatch.context() as m:
        m.setattr(sys, "exit", lambda _: True)
        with pytest.raises(RuntimeError) as exc:
            raise RuntimeError

        # Cause exception _inside_ the exception hook
        m.setattr(utils.pprint, "pformat", lambda _: 1 / 0)
        utils.hook_exceptions(exc.type, exc.value, exc.tb)

    assert "Uncaught exception! Quitting NormCap!" in caplog.text
    assert "debug output limited" in caplog.text
