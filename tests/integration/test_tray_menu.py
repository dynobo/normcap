from difflib import SequenceMatcher

import pytest
from PySide6 import QtGui

from normcap.gui.tray import screenshot

from .testcases import testcases


@pytest.mark.gui
def test_tray_menu_exit(monkeypatch, qtbot, qapp):
    """Test if application can be exited through tray icon."""
    # GIVEN NormCap is started to tray via "background-mode"
    # WHEN "exit" is clicked in system tray menu
    # THEN application should exit
    qapp.tray.tray_menu.show()
    exit_action = qapp.tray.tray_menu.findChild(QtGui.QAction, "exit")
    with qtbot.waitSignal(qapp.com.on_exit_application):
        exit_action.trigger()


@pytest.mark.gui
def test_tray_menu_capture(monkeypatch, qtbot, qapp, select_region):
    """Test if capture mode can be started through tray icon."""
    # GIVEN NormCap is started to tray via "background-mode"
    #       and with a certain test image as screenshot
    testcase = testcases[0]
    monkeypatch.setattr(screenshot, "capture", lambda: [testcase.screenshot])

    copy_to_clipboard_calls = {}
    monkeypatch.setattr(qapp, "_copy_to_clipboard", copy_to_clipboard_calls.update)

    # WHEN "capture" is clicked in system tray menu
    #      and a region on the screen is selected
    qapp.tray.tray_menu.show()

    capture_action = qapp.tray.tray_menu.findChild(QtGui.QAction, "capture")
    capture_action.trigger()

    # wait for windows to be created and moved on wayland
    qtbot.wait(50)

    select_region(on=qapp.windows[0], pos=testcase.coords)

    # THEN text should be captured
    #      and close to the ground truth
    #      and normcap should _not_ exit
    qtbot.waitUntil(lambda: copy_to_clipboard_calls != {})

    detected_text = copy_to_clipboard_calls["text"]
    similarity = SequenceMatcher(None, detected_text, testcase.expected_text).ratio()
    assert similarity >= 0.98, f"{detected_text=}"

    qtbot.assertNotEmitted(qapp.com.on_exit_application, wait=200)
