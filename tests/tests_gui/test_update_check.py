import urllib

import pytest

from normcap.gui import update_check
from normcap.gui.constants import URLS


@pytest.mark.skip_on_gh
@pytest.mark.parametrize("packaged", [True, False])
def test_update_checker_triggers_checked_signal(monkeypatch, qtbot, packaged):
    monkeypatch.setattr(update_check, "__version__", "0.0.0")
    checker = update_check.UpdateChecker(None, packaged=packaged)
    monkeypatch.setattr(checker, "_show_update_message", lambda *args, **kwargs: ...)
    with qtbot.waitSignal(checker.com.on_version_checked, timeout=2000) as _:
        checker.check()


@pytest.mark.skip_on_gh
@pytest.mark.parametrize("url", [URLS.releases_atom, URLS.pypi_json])
def test_urls_reachable(url):
    with urllib.request.urlopen(url) as response:
        assert response.code == 200


@pytest.mark.parametrize(
    "current, other, is_new",
    (
        ("0.3.15", "0.3.16", True),
        ("0.3.16", "0.3.15", False),
        ("0.3.15", "0.3.15", False),
        ("0.3.15", "0.13.14", True),
        ("0.3.15", "0.3.6", False),
        ("0.3.15", "0.3.15-beta1", False),
        ("0.3.15-beta3", "0.3.15-beta12", True),
        ("0.3.15-beta3", "0.3.15-alpha2", False),
        ("0.3.15-beta3", "0.3.15-alpha5", False),
    ),
)
def test_update_checker_is_new_version(current, other, is_new):
    assert (
        update_check.UpdateChecker._is_new_version(current=current, other=other)
        is is_new
    )


@pytest.mark.skip_on_gh
@pytest.mark.parametrize(
    "packaged,text",
    [(True, b"abc"), (False, b'{"no relevant":"info"}'), (False, b'{"invalid":"json"')],
)
def test_update_checker_cant_parse(qtbot, caplog, packaged, text):
    checker = update_check.UpdateChecker(None, packaged=packaged)
    with qtbot.waitSignal(
        checker.com.on_version_checked, raising=False, timeout=2000
    ) as result:
        checker._on_download_finished(text, "some url")

    assert not result.signal_triggered
    assert "ERROR" in caplog.text
