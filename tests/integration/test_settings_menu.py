import sys

import pytest
from PySide6 import QtWidgets

from normcap.gui.tray import screengrab

from .testcases import testcases


@pytest.mark.gui()
def test_settings_menu_creates_actions(monkeypatch, qtbot, run_normcap, test_signal):
    """Test if capture mode can be started through tray icon."""
    # GIVEN NormCap is started with any image as screenshot
    some_image = testcases[0].screenshot
    monkeypatch.setattr(screengrab, "capture", lambda: [some_image])
    monkeypatch.setattr(sys, "exit", test_signal.on_event.emit)
    tray = run_normcap(extra_cli_args=[])

    # WHEN the menu button is clicked (mocked here via aboutToShow, because menus are
    #    hard to test as they have their own event loops
    menu = tray.windows[0].findChild(QtWidgets.QToolButton, "settings_icon").menu()
    menu.aboutToShow.emit()
    qtbot.wait(200)

    # THEN various actions should be available in the menu
    actions = menu.actions()
    assert len(actions) > 10

    texts = [a.text().lower() for a in actions]
    assert "show notification" in texts
    assert "parse" in texts
    assert "languages" in texts
    assert "about" in texts
    assert "close" in texts


@pytest.mark.gui()
def test_settings_menu_close_action_exits(monkeypatch, qtbot, run_normcap, test_signal):
    """Tests complete OCR workflow."""
    # GIVEN NormCap is started with any image as screenshot
    #   and tray icon is disabled
    some_image = testcases[0].screenshot
    monkeypatch.setattr(screengrab, "capture", lambda: [some_image])
    monkeypatch.setattr(sys, "exit", test_signal.on_event.emit)
    tray = run_normcap(extra_cli_args=["--tray=False"])

    # WHEN the menu button is clicked (mocked here via aboutToShow, because menus are
    #    hard to test as they have their own event loops)
    #    and the "close" action is triggered
    menu = tray.windows[0].findChild(QtWidgets.QToolButton, "settings_icon").menu()
    menu.aboutToShow.emit()
    qtbot.wait(200)

    actions = menu.actions()
    close_action = next(a for a in actions if a.text().lower() == "close")
    with qtbot.waitSignal(test_signal.on_event) as blocker:
        close_action.trigger()

    # THEN normcap should exit with code 0
    assert blocker.args == [0]


@pytest.mark.gui()
def test_settings_menu_close_action_minimizes(
    monkeypatch, qtbot, run_normcap, test_signal
):
    """Tests complete OCR workflow."""
    # GIVEN NormCap is started with any image as screenshot
    #   and tray icon is enabled
    some_image = testcases[0].screenshot
    monkeypatch.setattr(screengrab, "capture", lambda: [some_image])
    monkeypatch.setattr(sys, "exit", test_signal.on_event.emit)
    tray = run_normcap(extra_cli_args=["--tray=True"])

    # WHEN the menu button is clicked (mocked here via aboutToShow, because menus are
    #    hard to test as they have their own event loops)
    #    and the "close" action is triggered
    menu = tray.windows[0].findChild(QtWidgets.QToolButton, "settings_icon").menu()
    menu.aboutToShow.emit()
    qtbot.wait(200)

    actions = menu.actions()
    close_action = next(a for a in actions if a.text().lower() == "close")
    close_action.trigger()

    # THEN normcap should not exit
    #   and all windows should be deleted
    qtbot.assertNotEmitted(test_signal.on_event, wait=200)
    assert tray.windows == {}
