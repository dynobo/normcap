from difflib import SequenceMatcher

import pytest

from normcap.gui.tray import screenshot

from .testcases import testcases


@pytest.mark.gui
@pytest.mark.parametrize("testcase", [t for t in testcases if not t.skip])
def test_normcap_ocr_testcases(
    monkeypatch, qtbot, testcase, qapp, select_region, test_signal
):
    """Tests complete OCR workflow."""

    # GIVEN NormCap is started with "language" set to english
    #        and --parse-text True (default)
    #        and a certain test image as screenshot
    monkeypatch.setattr(screenshot, "capture", lambda: [testcase.screenshot])
    monkeypatch.setattr(qapp.tray, "_set_tray_icon_done", test_signal.on_event.emit)

    copy_to_clipboard_calls = {}
    monkeypatch.setattr(qapp, "_copy_to_clipboard", copy_to_clipboard_calls.update)

    qapp._show_windows(delay_screenshot=False)
    # qtbot.waitUntil(lambda: len(qapp.windows) >= 1)

    # WHEN a certain test region is selected on the screen
    with qtbot.waitSignal(test_signal.on_event):
        select_region(on=qapp.windows[0], pos=testcase.coords)
        qtbot.waitUntil(lambda: copy_to_clipboard_calls != {}, timeout=7000)

    # THEN text should be captured
    #    and transformed by an appropriate transformer
    #    and result in a final text similar to the ground truth

    assert copy_to_clipboard_calls

    similarity = SequenceMatcher(
        None, copy_to_clipboard_calls["text"], testcase.expected_text
    ).ratio()
    assert similarity >= testcase.expected_similarity, (
        f"{testcase.image_path.name=}",
        f"{copy_to_clipboard_calls['text']=}",
        f"{testcase.expected_text=}",
    )
