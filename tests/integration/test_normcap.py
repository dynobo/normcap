from difflib import SequenceMatcher

import pytest

from normcap.gui.tray import screenshot, sys

from .testcases import testcases


@pytest.mark.gui
@pytest.mark.parametrize("testcase", [t for t in testcases if not t.skip])
def test_normcap_ocr_testcases(
    monkeypatch, qtbot, testcase, run_normcap, select_region, test_signal
):
    """Tests complete OCR workflow."""

    # GIVEN NormCap is started with "language" set to english
    #        and --parse-text True (default)
    #        and a certain test image as screenshot
    monkeypatch.setattr(screenshot, "capture", lambda: [testcase.screenshot])
    monkeypatch.setattr(sys, "exit", test_signal.on_event.emit)
    tray = run_normcap(extra_cli_args=["--language", "eng"])

    copy_to_clipboard_calls = {}
    monkeypatch.setattr(tray, "_copy_to_clipboard", copy_to_clipboard_calls.update)

    # WHEN a certain test region is selected on the screen
    with qtbot.waitSignal(test_signal.on_event) as blocker:
        select_region(on=tray.windows[0], pos=testcase.coords)
        qtbot.waitUntil(lambda: copy_to_clipboard_calls != {}, timeout=7000)

    # THEN normcap should exit with code 0
    #    and text should be captured
    #    and transformed by an appropriate transformer
    #    and result in a final text similar to the ground truth
    assert blocker.args == [0]

    assert copy_to_clipboard_calls

    assert copy_to_clipboard_calls["result_type"] in testcase.expected_text_type, (
        f"{testcase.image_path.name=}",
        f"{copy_to_clipboard_calls['text']=}",
        f"{testcase.expected_text=}",
    )

    assert copy_to_clipboard_calls["detector"] in testcase.expected_text_detector, (
        f"{testcase.image_path.name=}",
        f"{copy_to_clipboard_calls['detector'].detector=}",
        f"{testcase.expected_text_detector=}",
    )

    similarity = SequenceMatcher(
        None, copy_to_clipboard_calls["text"], testcase.expected_text
    ).ratio()
    assert similarity >= testcase.expected_similarity, (
        f"{testcase.image_path.name=}",
        f"{copy_to_clipboard_calls['text']=}",
        f"{testcase.expected_text=}",
    )
