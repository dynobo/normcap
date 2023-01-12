from pathlib import Path

from PySide6 import QtCore
from pytestqt.qtbot import QtBot

from normcap.gui import language_manager


def test_language_manager_download(monkeypatch, tmp_path, qtbot: QtBot):
    Path(tmp_path / "tessdata").mkdir()
    Path(tmp_path / "tessdata" / "eng.traineddata").touch()
    monkeypatch.setattr(
        language_manager.system_info, "config_directory", lambda: tmp_path
    )

    window = language_manager.LanguageManager()
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
