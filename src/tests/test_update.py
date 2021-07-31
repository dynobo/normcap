import pytest
from PySide2 import QtNetwork

from normcap.update_check import Downloader, UpdateChecker

# Allow pytest fixtures:
# pylint: disable=redefined-outer-name,protected-access


@pytest.mark.parametrize("packaged", [True, False])
def test_update_checker(qtbot, packaged):
    """Retrieve version information from github."""

    version_checker = UpdateChecker(packaged=packaged)

    with qtbot.waitSignal(version_checker.on_version_retrieved) as result:
        version_checker.check()
    version = result.args[0]

    assert isinstance(version, str)
    assert len(version) >= 5
    assert version[0].isdigit()
    assert version.count(".") == 2


@pytest.mark.parametrize(
    "packaged,text",
    [(True, "abc"), (False, '{"no relevant":"info"}'), (False, '{"invalid":"json"')],
)
def test_update_checker_cant_parse(caplog, packaged, text):
    """Retrieve version information from github."""

    version_checker = UpdateChecker(packaged=packaged)

    version = version_checker._parse_response(text)

    assert version == ""
    assert "ERROR" in caplog.text


def test_downloader(qtbot):
    """Download a website's source."""
    downloader = Downloader()
    with qtbot.waitSignal(downloader.on_download_finished) as result:
        downloader.get("https://github.com")

    raw = result.args[0]
    assert isinstance(raw, str)
    assert "</html>" in raw.lower()


def test_downloader_not_existing_url(qtbot):
    """Do not trigger download finished signal."""
    downloader = Downloader()
    with qtbot.waitSignal(
        downloader.on_download_finished, raising=False, timeout=2
    ) as result:
        downloader.get("http://not_existing_url.normcap")

    assert not result.args
    assert not result.signal_triggered


def test_downloader_network_error(caplog, qtbot):
    """Do not trigger download finished signal."""
    downloader = Downloader()

    class Reply(QtNetwork.QNetworkReply):
        """Reply stub"""

    reply = Reply()
    reply.setError(QtNetwork.QNetworkReply.HostNotFoundError, "Not Found")

    with qtbot.waitSignal(
        downloader.on_download_finished, raising=False, timeout=1
    ) as result:
        downloader._on_get_done(reply)

    assert not result.args
    assert not result.signal_triggered
    assert "ERROR" in caplog.text
