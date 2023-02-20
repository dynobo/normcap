from pathlib import Path

import pytest
from PySide6 import QtCore
from pytestqt.qtbot import QtBot

from normcap.gui import language_manager


@pytest.mark.gui
def test_download_language(monkeypatch, tmp_path, qtbot: QtBot):
    Path(tmp_path / "tessdata").mkdir()
    Path(tmp_path / "tessdata" / "eng.traineddata").touch()

    window = language_manager.LanguageManager(tessdata_path=tmp_path / "tessdata")
    window.show()
    qtbot.add_widget(window)

    assert len(window.installed_layout.model.languages) == 1
    assert window.installed_layout.model.languages[0][0] == "eng"

    qtbot.wait(200)
    qtbot.wait_active(window, timeout=5000)

    qtbot.mouseClick(
        window.available_layout.view.children()[0],
        QtCore.Qt.MouseButton.LeftButton,
        pos=QtCore.QPoint(10, 10),
        delay=500,
    )

    with qtbot.wait_signal(
        window.com.on_change_installed_languages, timeout=5000
    ) as result:
        qtbot.mouseClick(
            window.available_layout.button,
            QtCore.Qt.MouseButton.LeftButton,
        )

    assert result.signal_triggered
    assert result.args[0] == ["afr", "eng"]
    assert len(window.installed_layout.model.languages) == 2
    assert window.installed_layout.model.languages[0][0] == "afr"
    assert window.installed_layout.model.languages[1][0] == "eng"


def test_download_error_show_messagebox(qtbot, tmp_path, monkeypatch):
    result = []

    def mocked_messagebox(cls, title, message):
        result.append(f"{title} {message}")

    monkeypatch.setattr(
        language_manager.QtWidgets.QMessageBox, "critical", mocked_messagebox
    )

    Path(tmp_path / "tessdata").mkdir()
    Path(tmp_path / "tessdata" / "eng.traineddata").touch()

    window = language_manager.LanguageManager(tessdata_path=tmp_path / "tessdata")
    window.available_layout.model.languages = [("xyz", "9 MB", "none", "none")]
    window.available_layout.view.selectRow(0)

    with qtbot.wait_signal(window.downloader.com.on_download_failed):
        window._download()

    assert result
    assert "error" in result[0].lower()
    assert "xyz.traineddata" in result[0].lower()
