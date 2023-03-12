import logging
import urllib

import pytest
from PySide6 import QtWidgets

from normcap.gui import update_check
from normcap.gui.constants import URLS


@pytest.mark.skip_on_gh()
@pytest.mark.parametrize("packaged", [True, False])
def test_update_checker_triggers_checked_signal(monkeypatch, qtbot, packaged):
    monkeypatch.setattr(update_check, "__version__", "0.0.0")
    checker = update_check.UpdateChecker(None, packaged=packaged)
    monkeypatch.setattr(checker, "_show_update_message", lambda *args, **kwargs: ...)
    with qtbot.waitSignal(checker.com.on_version_checked, timeout=5000) as _:
        checker.check()


@pytest.mark.skip_on_gh()
@pytest.mark.parametrize("url", [URLS.releases_atom, URLS.pypi_json])
def test_urls_reachable(url):
    with urllib.request.urlopen(url) as response:
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


@pytest.mark.skip_on_gh()
@pytest.mark.parametrize(
    ("packaged", "text"),
    [(True, b"abc"), (False, b'{"no relevant":"info"}'), (False, "not binary")],
)
def test_update_checker_cant_parse(qtbot, caplog, packaged, text):
    checker = update_check.UpdateChecker(None, packaged=packaged)
    with qtbot.waitSignal(
        checker.com.on_version_checked, raising=False, timeout=2000
    ) as result:
        checker._on_download_finished(text, "some url")

    assert not result.signal_triggered
    assert "ERROR" in caplog.text


def test_show_update_message(qtbot, monkeypatch):
    checker = update_check.UpdateChecker(None)
    monkeypatch.setattr(checker.message_box, "exec_", lambda: QtWidgets.QMessageBox.Ok)

    version = "99.0.0"
    with qtbot.waitSignal(checker.com.on_click_get_new_version):
        checker._show_update_message(new_version=version)

    assert version in checker.message_box.text()


@pytest.mark.parametrize(
    ("packaged", "data", "message_args", "debug_log"),
    [
        (True, b"doesn't include version", [], "Could not detect remote version"),
        (True, "not-decodable", [], "Parsing response of update check failed"),
        (True, b'/releases/tag/v9.9.9"', ["9.9.9"], "Newest version: 9.9.9"),
        (False, b'"version": "9.9.9"', ["9.9.9"], "Newest version: 9.9.9"),
        (True, b'/releases/tag/v0.0.0"', [], "Newest version: 0.0.0"),
    ],
)
def test_on_download_finished(  # noqa:PLR0913
    caplog, qtbot, monkeypatch, packaged, data, message_args, debug_log
):
    args = []

    def mocked_show(new_version):
        args.append(new_version)

    checker = update_check.UpdateChecker(None)
    monkeypatch.setattr(checker, "packaged", packaged)
    monkeypatch.setattr(checker, "_show_update_message", mocked_show)

    with caplog.at_level(logging.DEBUG):
        checker._on_download_finished(data=data, url="")

    assert args == message_args
    assert debug_log in caplog.records[0].message
