import logging
import sys

import pytest
from PySide6 import QtCore

from normcap import argparser, logger_config


@pytest.mark.parametrize(
    ("xdg_session_type", "wayland_display", "expected_result"),
    [
        ("wayland", "", True),
        ("", "1", True),
        ("gnome", "", False),
        ("", "", False),
    ],
)
def test_is_wayland_display_manager(
    monkeypatch, xdg_session_type, wayland_display, expected_result
):
    # GIVEN the system has relevant env vars configured
    monkeypatch.setenv("XDG_SESSION_TYPE", xdg_session_type)
    monkeypatch.setenv("WAYLAND_DISPLAY", wayland_display)

    # WHEN it is checked for wayland
    result = logger_config._is_wayland_display_manager()

    # THEN is should return the corresponding result.
    assert result == expected_result


@pytest.mark.parametrize(
    ("arg_value", "expected_level"),
    [("info", logging.INFO), ("debug", logging.DEBUG)],
)
def test_prepare_logging(monkeypatch, arg_value, expected_level, caplog):
    with monkeypatch.context() as m:
        m.setattr(sys, "argv", [sys.argv[0], "--verbosity", arg_value])
        args = argparser.get_args()

    logger_config.prepare_logging(getattr(args, "verbosity", "ERROR"))
    logger = logging.getLogger("normcap")

    assert logger.getEffectiveLevel() == expected_level
    assert sys.excepthook == logger_config._hook_exceptions


def test_qt_log_wrapper(qtlog, caplog):
    logger = logging.getLogger(__name__).root
    logger.setLevel("DEBUG")
    QtCore.qDebug("should_show_in_qtlog_only")  # type: ignore # Wrong in PySide?

    QtCore.qInstallMessageHandler(logger_config._qt_log_wrapper)
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
    QtCore.qInstallMessageHandler(logger_config._qt_log_wrapper)

    QtCore.qDebug("Warning, OpenType support missing for OpenSans")  # type: ignore

    assert "[qt]" not in caplog.text.lower()
    assert "error" not in caplog.text.lower()


def test_qt_log_wrapper_no_platform_as_error(caplog):
    logger = logging.getLogger(__name__).root
    logger.setLevel("DEBUG")
    QtCore.qInstallMessageHandler(logger_config._qt_log_wrapper)

    QtCore.qDebug("could not load the qt platform")

    assert "could not load the qt platform" in caplog.text
    assert "[qt]" in caplog.text.lower()
    assert "error" in caplog.text.lower()


@pytest.mark.parametrize(
    ("is_wayland", "expected_package"),
    [(True, "qt6-wayland"), (False, "libxcb-cursor0")],
)
def test_qt_log_wrapper_platform_plugin_error_on_x(
    monkeypatch, caplog, is_wayland, expected_package
):
    # GIVEN the Qt-logger get's wrapped on a given desktop environment
    monkeypatch.setattr(
        logger_config, "_is_wayland_display_manager", lambda: is_wayland
    )
    logger = logging.getLogger(__name__).root
    logger.setLevel("DEBUG")
    QtCore.qInstallMessageHandler(logger_config._qt_log_wrapper)

    # WHEN the error caused by missing dependencies is logged
    QtCore.qDebug(
        "this application failed to start because no qt platform plugin could be "
        "initialized. reinstalling the application may fix this problem."
    )

    # THEN the log should contain the original qt log entry
    #    and a helpful message
    #    and it should mention the missing dependencies
    assert "[qt]" in caplog.text.lower()
    assert "no qt platform plugin could be initialized" in caplog.text

    assert "error" in caplog.text.lower()
    assert "make sure you have the following system packages" in caplog.text.lower()

    assert expected_package in caplog.text


def test_hook_exception(monkeypatch, caplog):
    # GIVEN a logger with level ERROR
    #   and a mocked sys.exit
    logger = logging.getLogger(__name__).root
    logger.setLevel("ERROR")
    exit_args = []

    def mocked_exit(code: int) -> None:
        exit_args.append(code)

    monkeypatch.setattr(sys, "exit", mocked_exit)

    # WHEN the exception hook is called
    test_message = "some test exception message"
    with pytest.raises(RuntimeError) as exc:
        raise RuntimeError(test_message)

    logger_config._hook_exceptions(exc.type, exc.value, exc.tb)

    # THEN there should be certain information in the logs
    #   and sys.exit should have been called with error code
    caplog_lower = caplog.text.lower()

    # Traceback:
    assert "uncaught exception!" in caplog_lower
    assert "traceback" in caplog_lower
    assert "exception" in caplog_lower
    assert "runtimeerror" in caplog_lower
    assert test_message in caplog_lower
    # System info:
    assert "system info" in caplog_lower
    assert "python_version" in caplog_lower
    # Issue request:
    assert "reporting this error" in caplog_lower

    assert exit_args == [1]
