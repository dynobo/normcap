import urllib

import pytest

from normcap.gui import update_check
from normcap.gui.constants import URLS


@pytest.mark.skip_on_gh
@pytest.mark.parametrize("packaged", [True, False])
def test_update_checker_new_version(monkeypatch, qtbot, packaged):
    monkeypatch.setattr(update_check, "__version__", "0.0.0")
    checker = update_check.UpdateChecker(None, packaged=packaged)
    monkeypatch.setattr(checker, "show_update_message", lambda args: ...)

    with qtbot.waitSignal(checker.com.on_new_version_found, timeout=4000) as result:
        checker.check()
    version = result.args[0]

    assert isinstance(version, str)
    assert len(version) >= 5
    assert version[0].isdigit()
    assert version.count(".") == 2


@pytest.mark.skip_on_gh
@pytest.mark.parametrize("url", [URLS.releases_atom, URLS.pypi_json])
def test_urls_reachable(url):
    with urllib.request.urlopen(url) as response:
        assert response.code == 200


@pytest.mark.skip_on_gh
@pytest.mark.parametrize("packaged", [True, False])
def test_update_checker_no_new_version(monkeypatch, qtbot, packaged):
    monkeypatch.setattr(update_check, "__version__", "9.9.9")
    checker = update_check.UpdateChecker(None, packaged=packaged)
    monkeypatch.setattr(checker, "show_update_message", lambda args: ...)

    with qtbot.waitSignal(
        checker.com.on_new_version_found, raising=False, timeout=4000
    ) as result:
        checker.check()
    assert not result.signal_triggered


@pytest.mark.skip_on_gh
@pytest.mark.parametrize(
    "packaged,text",
    [(True, "abc"), (False, '{"no relevant":"info"}'), (False, '{"invalid":"json"')],
)
def test_update_checker_cant_parse(qtbot, caplog, packaged, text):
    checker = update_check.UpdateChecker(None, packaged=packaged)
    with qtbot.waitSignal(
        checker.com.on_version_parsed, raising=False, timeout=4000
    ) as result:
        checker.parse_response_to_version(text)

    assert not result.signal_triggered
    assert "ERROR" in caplog.text
