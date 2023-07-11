import time
from difflib import SequenceMatcher

import pytest

from normcap.gui.tray import screengrab

from .testcases import testcases


@pytest.mark.gui()
@pytest.mark.parametrize("testcase", testcases)
def test_normcap_ocr_testcases(
    monkeypatch,
    qapp,
    qtbot,
    testcase,
    run_normcap,
    select_region,
    check_ocr_result,
):
    """Tests complete OCR workflow."""
    # GIVEN NormCap is started with "language" set to english
    #        and "parse"-mode
    #        and a certain test image as screenshot
    monkeypatch.setattr(
        screengrab, "get_capture_func", lambda: lambda: [testcase.image_scaled]
    )
    tray = run_normcap()

    # WHEN a certain test region is selected on the screen
    select_region(on=tray.windows[0], pos=testcase.coords_scaled)

    # THEN text should be captured, transformed by an appropriate magic
    #      and result in a final text close to the ground truth
    qtbot.waitUntil(check_ocr_result(tray), timeout=10_000)
    capture = tray.capture
    assert capture

    assert capture.ocr_applied_magic in testcase.ocr_magics, capture.ocr_text

    similarity = SequenceMatcher(
        None, capture.ocr_text, testcase.ocr_transformed
    ).ratio()
    assert similarity >= 0.98, f"{capture.ocr_text=}"

    time.sleep(1)
    tray.hide()
