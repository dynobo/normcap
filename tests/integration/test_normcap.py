from difflib import SequenceMatcher

import pytest

from normcap.gui.tray import screengrab, sys

from .testcases import testcases


@pytest.mark.gui()
@pytest.mark.parametrize("testcase", testcases)
def test_normcap_ocr_testcases(
    monkeypatch, qtbot, testcase, run_normcap, select_region, test_signal
):
    """Tests complete OCR workflow."""

    # GIVEN NormCap is started with "language" set to english
    #        and "parse"-mode
    #        and a certain test image as screenshot
    def mocked_capture_func():
        return lambda: [testcase.image_scaled]

    monkeypatch.setattr(screengrab, "get_capture_func", mocked_capture_func)
    monkeypatch.setattr(sys, "exit", lambda x: test_signal.on_event.emit(x))
    tray = run_normcap()

    # WHEN a certain test region is selected on the screen
    with qtbot.waitSignal(test_signal.on_event) as blocker:
        select_region(on=tray.windows[0], pos=testcase.coords_scaled)

    # THEN normcap should exit with code 0
    #    and text should be captured
    #    and transformed by an appropriate magic
    #    and result in a final text similar to the ground truth
    assert blocker.args == [0]

    capture = tray.capture
    assert capture

    assert capture.ocr_applied_magic in testcase.ocr_magics, capture.ocr_text

    similarity = SequenceMatcher(
        None, capture.ocr_text, testcase.ocr_transformed
    ).ratio()
    assert similarity >= 0.98, f"{capture.ocr_text=}"
