import os

import pytest
from pytestqt.qtbot import QtBot

from normcap.gui.downloader import Downloader, Worker


@pytest.mark.skipif("GITHUB_ACTIONS" in os.environ, reason="Skip on Action Runner")
def test_downloader_retrieves_website(qtbot: QtBot):
    # GIVEN a Downloader instance
    downloader = Downloader()

    # WHEN downloading an existing url
    test_url = "https://www.google.com"
    with qtbot.wait_signal(downloader.com.on_download_finished) as result:
        downloader.get(test_url)

    # THEN the triggered signal should receive raw data and the source url
    raw, url = result.args
    assert url == test_url
    assert isinstance(raw, bytes)
    assert "</html>" in raw.decode(encoding="utf-8", errors="ignore").lower()


def test_downloader_not_existing_url_does_not_trigger_finished(caplog, qtbot: QtBot):
    # GIVEN a Downloader instance
    downloader = Downloader()

    # WHEN downloading a not existing url
    wrong_url = "https://not_existing_url.normcap"

    # THEN the download finished signal should not be triggered
    #   and the exception messages should be logged
    with qtbot.assert_not_emitted(downloader.com.on_download_finished, wait=1000):
        downloader.get(wrong_url)
    assert "ERROR" in caplog.text
    assert wrong_url in caplog.text
    assert "Exception" in caplog.text


def test_downloader_not_existing_url_triggers_failed(caplog, qtbot: QtBot):
    # GIVEN a Downloader instance
    downloader = Downloader()

    # WHEN downloading a not existing url
    wrong_url = "https://not_existing_url.normcap"

    # THEN the download failed signal should be triggered
    #   and receive the exception and source url
    with qtbot.wait_signal(downloader.com.on_download_failed, timeout=1000) as result:
        downloader.get(wrong_url)

    assert result.signal_triggered
    assert wrong_url in result.args[0]
    assert "Exception" in result.args[0]


def test_worker_existing_url(qtbot):
    # GIVEN a downloader Worker instance is initialized with a valid url
    test_url = "https://github.com"
    worker = Worker(test_url)

    # WHEN the work is run
    with qtbot.waitSignal(worker.com.on_download_finished) as signal:
        worker.run()

    # THEN it should trigger the download finished signal
    #   and pass the raw data and source url as arguments
    assert type(signal.args[0]) is bytes
    assert signal.args[1] == test_url


def test_worker_not_existing_url(qtbot):
    # GIVEN a downloader Worker instance is initialized with a non existing url
    wrong_url = "https://not_existing_url.normcap"
    worker = Worker(wrong_url)

    # WHEN the work is run
    with qtbot.waitSignal(worker.com.on_download_failed) as signal:
        worker.run()

    # THEN it should trigger the download failed signal
    #   and pass the exception and source url as arguments
    assert signal.args[0].startswith("Exception")
    assert signal.args[1] == wrong_url
