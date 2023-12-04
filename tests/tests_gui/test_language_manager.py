from pathlib import Path
from urllib.error import URLError

import pytest
from pytestqt.qtbot import QtBot

from normcap.gui import language_manager


@pytest.mark.gui()
def test_download_language(tmp_path, qtbot: QtBot, mock_urlopen):
    # GIVEN only one language is installed
    Path(tmp_path / "tessdata").mkdir()
    Path(tmp_path / "tessdata" / "eng.traineddata").touch()
    mock_urlopen(b"SomeLanguageData")

    window = language_manager.LanguageManager(tessdata_path=tmp_path / "tessdata")
    qtbot.add_widget(window)

    assert len(window.installed_layout.model.languages) == 1
    assert window.installed_layout.model.languages[0][0] == "eng"

    # WHEN selecting the first available language
    #      and clicking the download button
    window.available_layout.view.selectRow(0)
    with qtbot.wait_signal(window.com.on_languages_changed, timeout=5000) as result:
        window.available_layout.button.click()

    # THEN another language gets installed
    #      and the change signal is trigger with the new installed languages as args
    assert len(window.installed_layout.model.languages) == 2
    assert window.installed_layout.model.languages[0][0] == "afr"
    assert window.installed_layout.model.languages[1][0] == "eng"

    assert result.signal_triggered
    assert result.args
    assert result.args[0] == ["afr", "eng"]


@pytest.mark.gui()
def test_delete_language(tmp_path, qtbot: QtBot):
    # GIVEN two languages are installed
    Path(tmp_path / "tessdata").mkdir()
    Path(tmp_path / "tessdata" / "deu.traineddata").touch()
    Path(tmp_path / "tessdata" / "eng.traineddata").touch()

    window = language_manager.LanguageManager(tessdata_path=tmp_path / "tessdata")
    qtbot.add_widget(window)

    assert len(window.installed_layout.model.languages) == 2
    assert window.installed_layout.model.languages[0][0] == "deu"

    # WHEN selecting the first available language
    #      and clicking the delete button
    window.installed_layout.view.selectRow(0)
    with qtbot.wait_signal(window.com.on_languages_changed, timeout=1000) as result:
        window.installed_layout.button.click()

    # THEN the first language gets deleted
    #      and the change signal is trigger with the remaining language as args
    assert len(window.installed_layout.model.languages) == 1
    assert window.installed_layout.model.languages[0][0] == "eng"

    assert result.signal_triggered
    assert result.args
    assert result.args[0] == ["eng"]


@pytest.mark.gui()
def test_delete_without_selection_does_nothing(monkeypatch, tmp_path, qtbot: QtBot):
    # GIVEN two languages are installed
    Path(tmp_path / "tessdata").mkdir()
    Path(tmp_path / "tessdata" / "deu.traineddata").touch()
    Path(tmp_path / "tessdata" / "eng.traineddata").touch()

    window = language_manager.LanguageManager(tessdata_path=tmp_path / "tessdata")
    qtbot.add_widget(window)

    assert len(window.installed_layout.model.languages) == 2
    assert window.installed_layout.model.languages[0][0] == "deu"

    # WHEN the clicking the delete button
    #      without selecting any entries
    window.installed_layout.view.clearSelection()
    with qtbot.wait_signal(
        window.com.on_languages_changed, timeout=100, raising=False
    ) as result:
        window.installed_layout.button.click()

    # THEN the language change signal is not triggered
    #      and no language get removed
    assert not result.signal_triggered

    assert len(window.installed_layout.model.languages) == 2
    assert window.installed_layout.model.languages[0][0] == "deu"


@pytest.mark.gui()
def test_delete_last_language_impossible(monkeypatch, tmp_path, qtbot: QtBot):
    # GIVEN only one language is installed
    messagebox_args = []
    monkeypatch.setattr(
        language_manager.QtWidgets.QMessageBox,
        "information",
        lambda parent, title, text: messagebox_args.extend([title, text]),
    )

    Path(tmp_path / "tessdata").mkdir()
    Path(tmp_path / "tessdata" / "eng.traineddata").touch()

    window = language_manager.LanguageManager(tessdata_path=tmp_path / "tessdata")
    qtbot.add_widget(window)

    assert len(window.installed_layout.model.languages) == 1
    assert window.installed_layout.model.languages[0][0] == "eng"

    # WHEN selecting the only language
    #      and clicking the delete button
    window.installed_layout.view.selectRow(0)
    with qtbot.wait_signal(
        window.com.on_languages_changed, timeout=100, raising=False
    ) as result:
        window.installed_layout.button.click()

    # THEN the language change signal is not triggered
    #      and no language get removed
    #      and the message box is displayed
    assert not result.signal_triggered

    assert len(window.installed_layout.model.languages) == 1
    assert window.installed_layout.model.languages[0][0] == "eng"

    assert "information" in messagebox_args[0].lower()
    assert "at least one" in messagebox_args[1].lower()


def test_download_error_show_messagebox(qtbot, tmp_path, monkeypatch, mock_urlopen):
    # GIVEN only one language is installed
    messagebox_args = []
    monkeypatch.setattr(
        language_manager.QtWidgets.QMessageBox,
        "critical",
        lambda parent, title, text: messagebox_args.extend([title, text]),
    )

    Path(tmp_path / "tessdata").mkdir()
    Path(tmp_path / "tessdata" / "eng.traineddata").touch()

    window = language_manager.LanguageManager(tessdata_path=tmp_path / "tessdata")
    qtbot.add_widget(window)

    # WHEN selecting an available language
    #      and clicking the download button
    #      and the download fails
    def _raise_error():
        raise URLError("http://un.known")

    mock_urlopen(response=None)

    window.available_layout.view.selectRow(0)
    with qtbot.wait_signal(window.downloader.com.on_download_failed):
        window.available_layout.button.click()

    # THEN the language change signal is not triggered
    #      and no language get removed
    #      and the message box is displayed
    assert messagebox_args
    assert "error" in messagebox_args[0].lower()
    assert "download failed" in messagebox_args[1].lower()
