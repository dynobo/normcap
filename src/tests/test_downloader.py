from PySide2 import QtNetwork

from normcap.gui.update_check import Downloader

# Allow pytest fixtures:
# pylint: disable=redefined-outer-name,protected-access


def test_downloader(qtbot):
    """Download a website's source."""
    downloader = Downloader()
    with qtbot.waitSignal(downloader.com.on_download_finished) as result:
        downloader.get("https://github.com")

    raw = result.args[0]
    assert isinstance(raw, str)
    assert "</html>" in raw.lower()


def test_downloader_not_existing_url(qtbot):
    """Do not trigger download finished signal."""
    downloader = Downloader()
    with qtbot.waitSignal(
        downloader.com.on_download_finished, raising=False, timeout=2
    ) as result:
        downloader.get("https://not_existing_url.normcap")

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
        downloader.com.on_download_failed, raising=False, timeout=1
    ) as result:
        downloader._on_get_finished(reply)

    assert not result.args
    assert result.signal_triggered
    assert "ERROR" in caplog.text
