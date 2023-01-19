import pytest
from pytestqt.qtbot import QtBot

from normcap.gui.downloader import Downloader


@pytest.mark.skip_on_gh
def test_downloader_retrieves_website(qtbot: QtBot):
    test_url = "https://www.google.com"
    downloader = Downloader()
    with qtbot.wait_signal(downloader.com.on_download_finished) as result:
        downloader.get(test_url)

    raw, url = result.args
    assert isinstance(raw, bytes)
    assert url == test_url

    text = raw.decode(encoding="utf-8", errors="ignore")
    assert "</html>" in text.lower()


def test_downloader_handles_not_existing_url(caplog, qtbot: QtBot):
    wrong_url = "https://not_existing_url.normcap"

    downloader = Downloader()
    # Do not trigger download finished signal on error
    with qtbot.assert_not_emitted(downloader.com.on_download_finished, wait=4000):
        downloader.get(wrong_url)

    assert "ERROR" in caplog.text
    assert wrong_url in caplog.text
    assert "Exception" in caplog.text

    # Do trigger download failed signal
    with qtbot.wait_signal(downloader.com.on_download_failed, timeout=4000) as result:
        downloader.get(wrong_url)

    assert result.signal_triggered
    assert wrong_url in result.args[0]
    assert "Exception" in result.args[0]
