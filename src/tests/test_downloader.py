import pytest

from normcap.gui.downloader_qtnetwork import Downloader as QtNetworkDownloader
from normcap.gui.downloader_requests import Downloader as RequestsDownloader

# Allow pytest fixtures:
# pylint: disable=redefined-outer-name,protected-access


@pytest.mark.skip_on_gh
@pytest.mark.parametrize("downloader", [QtNetworkDownloader(), RequestsDownloader()])
def test_downloader(qtbot, downloader):
    """Download a website's source."""
    with qtbot.waitSignal(downloader.com.on_download_finished) as result:
        downloader.get("https://www.google.com")

    raw = result.args[0]
    assert isinstance(raw, str)
    assert "</html>" in raw.lower()


@pytest.mark.parametrize("downloader", [RequestsDownloader(), QtNetworkDownloader()])
def test_downloader_not_existing_url(caplog, qtbot, downloader):
    """Do not trigger download finished signal."""

    # Do not trigger download finished signal
    with qtbot.waitSignal(
        downloader.com.on_download_finished, raising=False, timeout=3000
    ) as result:
        downloader.get("https://not_existing_url.normcap")

    assert not result.args
    assert not result.signal_triggered
    assert "ERROR" in caplog.text

    # Do trigger download failed signal
    with qtbot.waitSignal(downloader.com.on_download_failed, timeout=3000) as result:
        downloader.get("https://not_existing_url.normcap")

    assert result.signal_triggered
