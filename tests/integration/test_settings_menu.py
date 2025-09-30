import pytest
from PySide6 import QtWidgets

from normcap.gui.tray import screenshot

from .testcases import testcases


@pytest.mark.gui
def test_settings_menu_creates_actions(monkeypatch, qtbot, qapp):
    """Test if capture mode can be started through tray icon."""
    # GIVEN NormCap is started with any image as screenshot
    some_image = testcases[0].screenshot
    monkeypatch.setattr(screenshot, "capture", lambda: [some_image])
    qapp._show_windows(delay_screenshot=False)

    # WHEN the menu button is clicked (mocked here via aboutToShow, because menus are
    #    hard to test as they have their own event loops
    menu = qapp.windows[0].findChild(QtWidgets.QToolButton, "settings_icon").menu()
    menu.aboutToShow.emit()
    qtbot.wait(200)

    # THEN various actions should be available in the menu
    actions = menu.actions()
    assert len(actions) > 10

    texts = [a.text().lower() for a in actions]
    assert "show notification" in texts
    assert "parse text" in texts
    assert "languages" in texts
    assert "about" in texts
    assert "close" in texts


@pytest.mark.gui
def test_settings_menu_close_action_exits(monkeypatch, qtbot, qapp, test_signal):
    """Tests complete OCR workflow."""

    # GIVEN NormCap is started with any image as screenshot
    #   and tray icon is disabled
    some_image = testcases[0].screenshot
    monkeypatch.setattr(screenshot, "capture", lambda: [some_image])

    original_value_func = qapp.settings.value

    def _mocked_settings(*args, **kwargs):
        if "tray" in args:
            return False
        return original_value_func(*args, **kwargs)

    monkeypatch.setattr(qapp.settings, "value", _mocked_settings)
    qapp._show_windows(delay_screenshot=False)

    # WHEN the menu button is clicked (mocked here via aboutToShow, because menus are
    #    hard to test as they have their own event loops)
    #    and the "close" action is triggered
    menu = qapp.windows[0].findChild(QtWidgets.QToolButton, "settings_icon").menu()
    menu.aboutToShow.emit()
    qtbot.wait(200)

    actions = menu.actions()
    close_action = next(a for a in actions if a.text().lower() == "close")
    with qtbot.waitSignal(qapp.com.on_exit_application):
        close_action.trigger()


@pytest.mark.gui
def test_settings_menu_close_action_minimizes(monkeypatch, qtbot, qapp):
    """Tests complete OCR workflow."""
    # GIVEN NormCap is started with any image as screenshot
    #   and tray icon is enabled
    some_image = testcases[0].screenshot
    monkeypatch.setattr(screenshot, "capture", lambda: [some_image])
    qapp._show_windows(delay_screenshot=False)

    # WHEN the menu button is clicked (mocked here via aboutToShow, because menus are
    #    hard to test as they have their own event loops)
    #    and the "close" action is triggered
    menu = qapp.windows[0].findChild(QtWidgets.QToolButton, "settings_icon").menu()
    menu.aboutToShow.emit()
    qtbot.wait(200)

    with qtbot.waitSignal(qapp.com.on_windows_closed):
        actions = menu.actions()
        close_action = next(a for a in actions if a.text().lower() == "close")
        close_action.trigger()

    # THEN normcap should not exit
    #   and all windows should be deleted
    qtbot.assertNotEmitted(qapp.com.on_exit_application, wait=200)
    assert qapp.windows == {}
