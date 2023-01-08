from pathlib import Path

from normcap.gui import language_manager
from PySide6 import QtCore


def test_language_manager_download(monkeypatch, tmp_path, qtbot):
    Path(tmp_path / "tessdata").mkdir()
    Path(tmp_path / "tessdata" / "eng.traineddata").touch()
    monkeypatch.setattr(
        language_manager.system_info, "config_directory", lambda: tmp_path
    )

    language_dialog = language_manager.LanguageManager()
    assert len(language_dialog.installed_layout.model.languages) == 1
    assert language_dialog.installed_layout.model.languages[0][0] == "eng"

    def _close_button_has_focus():
        assert language_dialog.close_button.hasFocus()

    language_dialog.show()
    qtbot.wait_until(_close_button_has_focus, timeout=10000)

    qtbot.mouseClick(
        language_dialog.available_layout.view.children()[0],
        QtCore.Qt.MouseButton.LeftButton,
        pos=QtCore.QPoint(10, 10),
        delay=500,
    )

    with qtbot.wait_signal(
        language_dialog.com.on_change_installed_languages, timeout=5000
    ) as result:
        qtbot.mouseClick(
            language_dialog.available_layout.button,
            QtCore.Qt.MouseButton.LeftButton,
        )

    assert result.signal_triggered
    assert result.args[0] == ["afr", "eng"]
    assert len(language_dialog.installed_layout.model.languages) == 2
    assert language_dialog.installed_layout.model.languages[0][0] == "afr"
    assert language_dialog.installed_layout.model.languages[1][0] == "eng"
