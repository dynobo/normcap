import logging
import os
import urllib.request

import pytest
from PySide6 import QtWidgets

from normcap.gui import downloader, update_check
from normcap.gui.constants import URLS


@pytest.mark.parametrize("packaged", [True, False])
@pytest.mark.skipif("GITHUB_ACTIONS" in os.environ, reason="Skip on Action Runner")
def test_update_checker_triggers_checked_signal(monkeypatch, qtbot, packaged):
    # GIVEN we have an older version
    monkeypatch.setattr(update_check, "__version__", "0.0.0")
    checker = update_check.UpdateChecker(None, packaged=packaged)

    show_message_args = {}

    def _mocked_show_update_message(**kwargs):
        show_message_args.update(kwargs)

    monkeypatch.setattr(checker, "_show_update_message", _mocked_show_update_message)

    # WHEN the update check is performed
    with qtbot.waitSignal(checker.com.on_version_checked, timeout=5000) as result:
        checker.com.check.emit()

    # THEN a signal should be send with the new version
    #    and the version should also be displayed in the message
    #    and the version should be a valid one (major.minor.patch)
    assert result.signal_triggered
    assert result.args[0] == show_message_args["version"]
    assert len(result.args[0].split(".")) == 3


@pytest.mark.parametrize("url", [URLS.releases_atom, URLS.pypi_json])
@pytest.mark.skipif("GITHUB_ACTIONS" in os.environ, reason="Skip on Action Runner")
def test_urls_reachable(url):
    """Test if the URLs which contain the release information are reachable."""
    with urllib.request.urlopen(url) as response:  # noqa: S310
        assert response.code == 200


@pytest.mark.parametrize(
    ("current", "other", "is_new"),
    [
        ("0.3.15", "0.3.16", True),
        ("0.3.16", "0.3.15", False),
        ("0.3.15", "0.3.15", False),
        ("0.3.15", "0.13.14", True),
        ("0.3.15", "0.3.6", False),
        ("0.3.15", "0.3.15-beta1", False),
        ("0.3.15-beta3", "0.3.15-beta12", False),
        ("0.3.15-beta3", "0.3.15-alpha5", False),
        ("0.3.15-beta3", "0.3.15", False),
        ("0.3.15-beta3", "0.3.16", True),
    ],
)
def test_update_checker_is_new_version(current, other, is_new):
    assert (
        update_check.UpdateChecker._is_new_version(current=current, other=other)
        is is_new
    )


@pytest.mark.parametrize(
    ("packaged", "text"),
    [(True, b"abc"), (False, b'{"no relevant":"info"}'), (False, "not binary")],
)
@pytest.mark.skipif("GITHUB_ACTIONS" in os.environ, reason="Skip on Action Runner")
def test_update_checker_cant_parse(qtbot, caplog, packaged, text):
    # GIVEN an update checker is instantiated for
    #    either bundled NormCap or plain Python NormCap
    checker = update_check.UpdateChecker(None, packaged=packaged)

    # WHEN the download finished receives the (mocked) download response
    #    with unexpected/broken data
    with qtbot.waitSignal(
        checker.com.on_version_checked, raising=False, timeout=200
    ) as result:
        checker._on_download_finished(text, "some url")

    # THEN version checked event should not be triggered
    #    and error information should be logged
    assert not result.signal_triggered
    assert "ERROR" in caplog.text


def test_show_update_message(qtbot, monkeypatch):
    # GIVEN a UpdateChecker
    checker = update_check.UpdateChecker(None)
    monkeypatch.setattr(
        checker.message_box, "exec", lambda: QtWidgets.QMessageBox.StandardButton.Ok
    )

    # WHEN the method to show "New version available" message is called
    version = "99.0.0"
    with qtbot.waitSignal(checker.com.on_click_get_new_version):
        checker._show_update_message(version=version)

    # THEN the message box should contain the version
    assert version in checker.message_box.text()


@pytest.mark.parametrize(
    (
        "packaged",
        "data",
        "expected_show_message_args",
        "expected_log",
        "expected_triggered",
    ),
    [
        (True, b'/releases/tag/v9.9.9"', ["9.9.9"], "Newest version: 9.9.9", True),
        (True, b'/releases/tag/v0.0.0"', [], "Newest version: 0.0.0", True),
        (False, b'"version": "9.9.9"', ["9.9.9"], "Newest version: 9.9.9", True),
        (True, b"doesn't include version", [], "Could not detect remote", False),
        (True, "not-decodable", [], "Parsing response of update check failed", False),
    ],
)
def test_on_download_finished(
    caplog,
    qtbot,
    monkeypatch,
    packaged,
    data,
    expected_show_message_args,
    expected_log,
    expected_triggered,
):
    # GIVEN a (un)packaged version of NormCap
    #   and a mocked response for the request to the version url
    checker = update_check.UpdateChecker(parent=None, packaged=packaged)

    args = []

    def mocked_show_update_message(version):
        args.append(version)

    monkeypatch.setattr(checker, "_show_update_message", mocked_show_update_message)

    def _mocked_downloader_get(cls, url: str, timeout: float):
        cls.com.on_download_finished.emit(data, url)

    monkeypatch.setattr(downloader.Downloader, "get", _mocked_downloader_get)

    # WHEN the update check is triggered (with debug log level)
    with (
        caplog.at_level(logging.DEBUG),
        qtbot.wait_signal(
            checker.com.on_version_checked, timeout=200, raising=False
        ) as result,
    ):
        checker.com.check.emit()

    # THEN the update message is (not) shown with certain text
    #    and certain messages are logged
    assert result.signal_triggered == expected_triggered
    assert args == expected_show_message_args
    assert expected_log in caplog.text
