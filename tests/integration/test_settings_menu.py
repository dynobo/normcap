import sys
from difflib import SequenceMatcher

import pytest

from normcap import app
from normcap.gui.tray import screengrab

from .testcases import testcases


# TODO: Not yet implemented!
@pytest.mark.gui()
def test_settings_menu_capture(
    monkeypatch, qapp, qtbot, cli_args, select_region, check_ocr_result
):
    """Test if capture mode can be started through tray icon."""
    # GIVEN NormCap is started with "show in tray" enabled in "background-mode"
    #       and a certain test image as screenshot
    monkeypatch.setattr(sys, "argv", cli_args)
    testcase = testcases[0]
    monkeypatch.setattr(
        screengrab, "get_capture_func", lambda: lambda: [testcase.image_scaled]
    )

    monkeypatch.setattr(app, "_get_application", lambda: qapp)
    _, tray = app._prepare_app_and_tray()

    # WHEN "capture" is clicked in system tray menu
    #      and a region on the screen is selected
    select_region(on=tray.windows[0], pos=testcase.coords_scaled)

    # THEN text should be captured and close to the ground truth
    qtbot.waitUntil(check_ocr_result(tray))
    capture = tray.capture
    assert capture

    similarity = SequenceMatcher(
        None, capture.ocr_text, testcase.ocr_transformed
    ).ratio()
    assert similarity >= 0.98, f"{capture.ocr_text=}"

    tray.hide()
    tray.deleteLater()
