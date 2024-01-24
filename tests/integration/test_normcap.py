from difflib import SequenceMatcher

import pytest

from normcap.gui.tray import screengrab, sys

from .testcases import testcases


@pytest.mark.gui()
@pytest.mark.parametrize("testcase", [t for t in testcases if not t.skip])
def test_normcap_ocr_testcases(
    monkeypatch, qtbot, testcase, run_normcap, select_region, test_signal
):
    """Tests complete OCR workflow."""

    # GIVEN NormCap is started with "language" set to english
    #        and "parse"-mode
    #        and a certain test image as screenshot
    monkeypatch.setattr(screengrab, "capture", lambda: [testcase.screenshot])
    monkeypatch.setattr(sys, "exit", test_signal.on_event.emit)
    tray = run_normcap(extra_cli_args=["--language", "eng"])

    # WHEN a certain test region is selected on the screen
    with qtbot.waitSignal(test_signal.on_event) as blocker:
        select_region(on=tray.windows[0], pos=testcase.coords)

    # THEN normcap should exit with code 0
    #    and text should be captured
    #    and transformed by an appropriate transformer
    #    and result in a final text similar to the ground truth
    assert blocker.args == [0]

    capture = tray.capture
    assert capture

    assert capture.ocr_transformer in testcase.expected_ocr_transformers, (
        f"{testcase.image_path.name=}",
        f"{capture.ocr_text=}",
        f"{testcase.expected_ocr_text=}",
    )

    similarity = SequenceMatcher(
        None, capture.ocr_text, testcase.expected_ocr_text
    ).ratio()

    assert similarity >= testcase.expected_similarity, (
        f"{testcase.image_path.name=}",
        f"{capture.ocr_text=}",
        f"{testcase.expected_ocr_text=}",
    )
