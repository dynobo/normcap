import sys
from difflib import SequenceMatcher

import pytest
from PySide6 import QtGui

from normcap.gui.tray import screengrab

from .testcases import testcases


@pytest.mark.gui()
def test_tray_menu_exit(monkeypatch, qtbot, run_normcap):
    """Test if application can be exited through tray icon."""
    # GIVEN NormCap is started to tray via "background-mode"
    tray = run_normcap(extra_cli_args=["--background-mode"])

    exit_calls = []
    monkeypatch.setattr(sys, "exit", exit_calls.append)

    # WHEN "exit" is clicked in system tray menu
    tray.tray_menu.show()
    exit_action = tray.tray_menu.findChild(QtGui.QAction, "exit")
    exit_action.trigger()

    # THEN the NormCap should exit with exit code 0
    qtbot.waitUntil(lambda: len(exit_calls) > 0)
    assert exit_calls == [0]


@pytest.mark.gui()
def test_tray_menu_capture(monkeypatch, qtbot, run_normcap, select_region):
    """Test if capture mode can be started through tray icon."""
    # GIVEN NormCap is started to tray via "background-mode"
    #       and with a certain test image as screenshot
    tray = run_normcap(
        extra_cli_args=["--language=eng", "--mode=parse", "--background-mode"]
    )
    assert not tray.windows

    testcase = testcases[0]
    monkeypatch.setattr(screengrab, "capture", lambda: [testcase.screenshot])

    exit_calls = []
    monkeypatch.setattr(sys, "exit", exit_calls.append)

    # WHEN "capture" is clicked in system tray menu
    #      and a region on the screen is selected
    tray.tray_menu.show()

    capture_action = tray.tray_menu.findChild(QtGui.QAction, "capture")
    capture_action.trigger()

    # wait for windows to be created and moved on wayland
    qtbot.wait(50)

    select_region(on=tray.windows[0], pos=testcase.coords)

    # THEN text should be captured
    #      and close to the ground truth
    #      and normcap should _not_ exit
    qtbot.waitUntil(lambda: tray.capture.ocr_text is not None)

    capture = tray.capture
    assert capture

    similarity = SequenceMatcher(
        None, capture.ocr_text, testcase.expected_ocr_text
    ).ratio()
    assert similarity >= 0.98, f"{capture.ocr_text=}"

    assert not exit_calls
